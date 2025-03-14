"""
This is a pipeline for generating YouTube shorts scripts.
"""

from kedro.pipeline import Pipeline, node
from kedro.pipeline.modular_pipeline import pipeline

from .nodes import generate_youtube_short_script, save_script


def create_pipeline(**kwargs) -> Pipeline:
    """
    Create a pipeline for generating YouTube shorts scripts.
    
    Returns:
        A Kedro Pipeline object.
    """
    return pipeline(
        [
            node(
                func=generate_youtube_short_script,
                inputs=["params:topic"],
                outputs="youtube_script",
                name="generate_youtube_script_node",
            ),
            node(
                func=save_script,
                inputs=["youtube_script", "params:save_script"],
                outputs="script_path",
                name="save_script_node",
            ),
        ]
    ) 