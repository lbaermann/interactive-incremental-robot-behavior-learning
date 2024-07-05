import sys
from pathlib import Path


def sum_costs_from_logfile(p: Path):
    lines = p.read_text().splitlines()
    cost_prefix = 'Total Cost (USD): $'
    prompt_tokens_prefix = '	Prompt Tokens:'
    completion_tokens_prefix = '	Completion Tokens:'
    total_cost = 0
    total_prompt_tokens, total_completion_tokens = 0, 0
    for line in lines:
        if line.startswith(cost_prefix):
            number = line[len(cost_prefix):]
            total_cost += float(number)
        if line.startswith(prompt_tokens_prefix):
            number = line[len(prompt_tokens_prefix):]
            total_prompt_tokens += int(number)
        if line.startswith(completion_tokens_prefix):
            number = line[len(completion_tokens_prefix):]
            total_completion_tokens += int(number)

    print('prompt tokens:    ', total_prompt_tokens)
    print('completion tokens:', total_completion_tokens)
    print('                 $', total_cost)


if __name__ == '__main__':
    sum_costs_from_logfile(Path(sys.argv[1]))
