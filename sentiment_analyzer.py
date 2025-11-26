from typing import Any, Dict, Text

from rasa.engine.graph import GraphComponent
from rasa.engine.recipes.default_recipe import DefaultV1Recipe
from rasa.shared.nlu.training_data.message import Message
from rasa.shared.nlu.training_data.training_data import TrainingData
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


@DefaultV1Recipe.register([GraphComponent], is_trainable=False)
class SentimentAnalyzer(GraphComponent):
    """A custom NLU component for sentiment analysis using VADER."""

    def __init__(self, config: Dict[Text, Any]) -> None:
        self.config = config
        self.analyzer = SentimentIntensityAnalyzer()

    @staticmethod
    def get_default_config() -> Dict[Text, Any]:
        """Default configuration for the component."""
        return {"threshold": -0.05}

    def train(
        self,
        training_data: TrainingData,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """This component is not trainable."""
        pass

    def process(self, message: Message, **kwargs: Any) -> None:
        """Analyze sentiment and either add an entity OR override the intent."""

        sentiment = self.analyzer.polarity_scores(message.get("text"))
        compound_score = sentiment["compound"]

        # Set a threshold for negative sentiment
        NEGATIVE_THRESHOLD = -0.05

        POSITIVE_THRESHOLD = 0.4

        if compound_score < NEGATIVE_THRESHOLD:
            # 1. Create the entity (still useful for logs)
            entity = {
                "entity": "sentiment",
                "value": "negative",
                "confidence": 1.0 - compound_score,
                "extractor": self.name,
            }
            message.set(
                "entities", message.get("entities", []) + [entity], add_to_output=True
            )

            # Create a new intent object with 100% confidence
            intent = {
                "name": "negative_sentiment",
                "confidence": 1.0,
            }

            # Get existing intent ranking and put our new intent at the front
            intent_ranking = message.get("intent_ranking", [])
            intent_ranking.insert(0, intent)  # Add to the top

            # Set the message's top intent
            message.set("intent", intent, add_to_output=True)
            message.set("intent_ranking", intent_ranking, add_to_output=True)

        elif compound_score > POSITIVE_THRESHOLD:
            # If the user is very happy, set a 'positive_sentiment' intent
            intent = {
                "name": "positive_sentiment",
                "confidence": 1.0,
            }
            intent_ranking = message.get("intent_ranking", [])
            intent_ranking.insert(0, intent)
            message.set("intent", intent, add_to_output=True)
            message.set("intent_ranking", intent_ranking, add_to_output=True)

    def persist(self) -> None:
        """This component has nothing to persist."""
        pass
