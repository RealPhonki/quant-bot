# project
from src.stock_client import StockClient
from src.evaluator import Evaluator
from src.game import Game

# TODO: determine format for args

class App:
    def __init__(self) -> None:
        self.stock_client = StockClient()

    def parse_args(self) -> None:
        pass

    def run(self) -> None:
        pass

    def run_evaluation(self) -> None:
        pass

    def run_game(self) -> None:
        pass

if __name__ == "__main__":
    app = App()
    app.run()