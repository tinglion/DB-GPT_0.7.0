"""Summary Assistant Agent."""

import logging
from typing import Dict, List, Optional, Tuple

from dbgpt.rag.retriever.rerank import RetrieverNameRanker

from .. import AgentMessage
from ..core.action.blank_action import BlankAction
from ..core.base_agent import ConversableAgent
from ..core.profile import DynConfig, ProfileConfig

logger = logging.getLogger(__name__)


class SummaryAssistantAgent(ConversableAgent):
    """Summary Assistant Agent."""

    profile: ProfileConfig = ProfileConfig(
        name=DynConfig(
            "Aristotle",
            category="agent",
            key="dbgpt_agent_expand_summary_assistant_agent_profile_name",
        ),
        role=DynConfig(
            "Summarizer",
            category="agent",
            key="dbgpt_agent_expand_summary_assistant_agent_profile_role",
        ),
        goal=DynConfig(
            "Summarize and analyze the provided resource information or historical conversation memories based on user questions. "
            "Generate concise summaries and organize relevant data, optionally presenting results through appropriate visualizations.",
            category="agent",
            key="dbgpt_agent_expand_summary_assistant_agent_profile_goal",
        ),
        constraints=DynConfig(
            [
                "Prioritize summarizing answers to user questions using the provided resource text. If no relevant content exists, attempt to extract from historical dialogue memory.",
                "Never fabricate information — only use what is explicitly provided or available in memory.",
                "Identify the core question posed by the user before performing any summarization or analysis.",
                "Extract and preprocess relevant information from input data for summarization and structured output.",
                "Only output content directly related to the user's question, using the same language as the user’s query.",
                "If no relevant information is found, respond with: 'Did not find the information you want.'",
                "Perform basic data organization (e.g., categorization, tabulation) if required to support visualization decisions.",
                "Select an appropriate display method from supported types to visualize results. If no suitable type exists, default to 'response_table'. "
                "Supported types:\n{{ display_type }}",
                """Please reply strictly in the following json format:
```vis-db-chart\\n
{
    "display_type": "The chart rendering method selected for SQL. If you don’t know what to output, just output 'response_table' uniformly.",
    "sql":"",
    "data": [{},{}],
    "thought": "Summary of thoughts to the user"
}
```
        Make sure the reply content only has the correct json.""",
            ],
            # TODO 固定输出格式
            # markdown="```vis-db-chart\\n{
            # "sql": "SELECT FLOOR(fd_1734072340307 / 10) * 10 AS age_group, COUNT(*) AS count FROM t_crf_123 GROUP BY age_group;",
            # "type": "response_pie_chart",
            # "title": "",
            # "describe": "根据用户需求，将年龄以10岁为区间进行分组统计，并用饼图表示各年龄段的人数分布。",
            # "data"}
            category="agent",
            key="dbgpt_agent_expand_summary_assistant_agent_profile_constraints",
        ),
        desc=DynConfig(
            "This agent analyzes and summarizes provided or historical text data according to user questions, organizes key information, and selects appropriate visual representations to enhance understanding.",
            category="agent",
            key="dbgpt_agent_expand_summary_assistant_agent_profile_desc",
        ),
    )

    def __init__(self, **kwargs):
        """Create a new SummaryAssistantAgent instance."""
        super().__init__(**kwargs)
        self._post_reranks = [RetrieverNameRanker(5)]
        self._init_actions([BlankAction])

    async def load_resource(self, question: str, is_retry_chat: bool = False):
        """Load agent bind resource."""
        if self.resource:
            if self.resource.is_pack:
                sub_resources = self.resource.sub_resources
                candidates_results: List = []
                resource_candidates_map = {}
                info_map = {}
                prompt_list = []
                for resource in sub_resources:
                    (
                        candidates,
                        prompt_template,
                        resource_reference,
                    ) = await resource.get_resources(question=question)
                    resource_candidates_map[resource.name] = (
                        candidates,
                        resource_reference,
                        prompt_template,
                    )
                    candidates_results.extend(candidates)  # type: ignore # noqa
                new_candidates_map = self.post_filters(resource_candidates_map)
                for resource, (
                    candidates,
                    references,
                    prompt_template,
                ) in new_candidates_map.items():
                    content = "\n".join(
                        [
                            f"--{i}--:" + chunk.content
                            for i, chunk in enumerate(candidates)  # type: ignore # noqa
                        ]
                    )
                    prompt_list.append(
                        prompt_template.format(name=resource, content=content)
                    )
                    info_map.update(references)
                return "\n".join(prompt_list), info_map
            else:
                resource_prompt, resource_reference = await self.resource.get_prompt(
                    lang=self.language, question=question
                )
                return resource_prompt, resource_reference
        return None, None

    def _init_reply_message(
        self,
        received_message: AgentMessage,
        rely_messages: Optional[List[AgentMessage]] = None,
    ) -> AgentMessage:
        reply_message = super()._init_reply_message(received_message, rely_messages)
        reply_message.context = {
            "display_type": """response_line_chart:used to display comparative trend analysis data
response_pie_chart:suitable for scenarios such as proportion and distribution statistics
response_table:suitable for display with many display columns or non-numeric columns
response_scatter_chart:Suitable for exploring relationships between variables, detecting outliers, etc.
response_bubble_chart:Suitable for relationships between multiple variables, highlighting outliers or special situations, etc.
response_donut_chart:Suitable for hierarchical structure representation, category proportion display and highlighting key categories, etc.
response_area_chart:Suitable for visualization of time series data, comparison of multiple groups of data, analysis of data change trends, etc.
response_heatmap:Suitable for visual analysis of time series data, large-scale data sets, distribution of classified data, etc.
""",
            "user_question": received_message.content,
        }
        return reply_message

    def post_filters(self, resource_candidates_map: Optional[Dict[str, Tuple]] = None):
        """Post filters for resource candidates."""
        if resource_candidates_map:
            new_candidates_map = resource_candidates_map.copy()
            filter_hit = False
            for resource, (
                candidates,
                references,
                prompt_template,
            ) in resource_candidates_map.items():
                for rerank in self._post_reranks:
                    filter_candidates = rerank.rank(candidates)
                    new_candidates_map[resource] = [], [], prompt_template
                    if filter_candidates and len(filter_candidates) > 0:
                        new_candidates_map[resource] = (
                            filter_candidates,
                            references,
                            prompt_template,
                        )
                        filter_hit = True
                        break
            if filter_hit:
                logger.info("Post filters hit, use new candidates.")
                return new_candidates_map
        return resource_candidates_map
