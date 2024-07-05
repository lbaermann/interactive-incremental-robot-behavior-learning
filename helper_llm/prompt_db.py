import json
from functools import cached_property
from pathlib import Path
from typing import List


class HelperPromptDB:
    def __init__(self, prompt_base_dir: Path = Path(__file__).parent / 'prompts'):
        super().__init__()
        self.prompt_plan = (prompt_base_dir / 'prompt_plan.txt').read_text().strip()
        self.prompt_replan = (prompt_base_dir / 'prompt_replan.txt').read_text().strip()
        self.examples = [
            f.read_text().strip()
            for f in (prompt_base_dir / 'examples').iterdir()
        ]
        self.examples_errors = [
            f.read_text().strip()
            for f in (prompt_base_dir / 'example_errors').iterdir()
        ]
        self.learned_samples_file = prompt_base_dir / 'learned_samples.json'

    @cached_property
    def learned_samples(self) -> List[str]:
        if not self.learned_samples_file.is_file():
            return []
        return json.loads(self.learned_samples_file.read_text())

    @property
    def all_examples(self):
        return self.examples + self.learned_samples

    def store_new_example(self, example: str):
        new_samples = self.learned_samples + [example]
        self.learned_samples_file.write_text(json.dumps(new_samples))
        # noinspection PyPropertyAccess
        del self.learned_samples  # Invalidate cache
