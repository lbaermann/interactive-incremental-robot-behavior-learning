import json
import sys
from pathlib import Path
from pprint import pprint
from typing import List

import numpy as np


def _read_results_file(file: Path):
    d: dict = json.loads(file.read_text())
    stats = {
        k: {r: [] for r in ('success', 'failure', 'error', 'timeout', 'initial_success',
                            'learn_from_interaction_calls', 'fixed_trough_interaction', 'user_interaction',
                            'num_interactions_until_success')}
        for k in d.keys()
    }
    metrics_per_experiment = [{
        k: 0 for k in ('success', 'initial_success', 'num_interactions_until_success')
    } for _ in range(len(next(iter(d.values()))))]
    for k, all_runs in d.items():
        for i, (interaction_list, transcript) in enumerate(all_runs):
            final_result = interaction_list[-1][1]
            stats[k][final_result].append(i)
            if 'learn_from_interaction()' in transcript:
                stats[k]['learn_from_interaction_calls'].append(i)
            if len(interaction_list) > 1:
                stats[k]['user_interaction'].append(i)
            if len(interaction_list) > 1 and interaction_list[0][1] != 'success' and final_result == 'success':
                stats[k]['fixed_trough_interaction'].append(i)
            if final_result == 'success':
                num_interactions_until_success = min(j for j, x in enumerate(interaction_list) if x[1] == 'success')
                stats[k]['num_interactions_until_success'].append(num_interactions_until_success)
                metrics_per_experiment[i]['success'] += 1
                metrics_per_experiment[i]['num_interactions_until_success'] += num_interactions_until_success
            if interaction_list[0][1] == 'success':
                stats[k]['initial_success'].append(i)
                metrics_per_experiment[i]['initial_success'] += 1
        stats[k]['success_rate'] = len(stats[k]['success']) / len(all_runs)
        stats[k]['initial_success_rate'] = len(stats[k]['initial_success']) / len(all_runs)
        stats[k]['avg_num_interactions_until_success'] = (
            sum(stats[k]['num_interactions_until_success']) / len(stats[k]['success'])
            if len(stats[k]['success']) > 0 else -1)

    for i, per_experiment in enumerate(metrics_per_experiment):
        per_experiment['avg_num_interactions_until_success'] = (per_experiment['num_interactions_until_success']
                                                                / max(per_experiment['success'], 1))
        per_experiment['initial_success_rate'] = per_experiment['initial_success'] / len(d)

    stats['total'] = {
        'success': sum(v['success_rate'] for v in stats.values()) / len(stats),
        'initial_success': sum(v['initial_success_rate'] for v in stats.values()) / len(stats),
        'num_interactions_until_success': sum(max(0, v['avg_num_interactions_until_success'])
                                              for v in stats.values()
                                              ) / sum(1 for v in stats.values()
                                                      if v['avg_num_interactions_until_success'] >= 0)
    }

    return stats, metrics_per_experiment


def main(file: Path):
    stats, metrics_per_experiment = _read_results_file(file)

    for k, result in stats.items():
        print(k)
        pprint(result)
        print()

    print()

    for i, metrics in enumerate(metrics_per_experiment):
        print(i, metrics['initial_success'] / len(stats),
              metrics['num_interactions_until_success'] / max(1, metrics['success']))

    print('\n' * 3)
    print('split & success & init. success & num inter. until success')
    max_len = max(len(k) for k in stats.keys())
    for k, result in stats.items():
        if k != 'total':
            print(k + ' ' * (max_len - len(k)),
                  result['success_rate'] * 100,
                  result['initial_success_rate'] * 100,
                  round(result['avg_num_interactions_until_success'], 2),
                  sep=' & ')
    print(max_len * ' ',
          round(stats['total']['success'] * 100, 1),
          round(stats['total']['initial_success'] * 100, 1),
          round(stats['total']['num_interactions_until_success'], 2),
          sep=' & ')


def eval_global_per_round_num_interactions_until_success(paths: List[Path]):
    print('Reading', paths)
    global_metrics_per_experiment = None
    for p in paths:
        _, metrics = _read_results_file(p)
        if global_metrics_per_experiment is None:
            global_metrics_per_experiment = [
                {
                    k: [v]
                    for k, v in m.items()
                } for m in metrics
            ]
        else:
            for g, l in zip(global_metrics_per_experiment, metrics):
                for k in l.keys():
                    g[k].append(l[k])

    for i, per_experiment in enumerate(global_metrics_per_experiment):
        for k, values in list(per_experiment.items()):
            per_experiment[k] = np.average(values), np.std(values)

    print('x i err')
    for i, per_experiment in enumerate(global_metrics_per_experiment):
        n, err = per_experiment["initial_success_rate"]
        #n, err = per_experiment["avg_num_interactions_until_success"]
        print(i + 1, n, err)


if __name__ == '__main__':
    main(Path(sys.argv[1]))
    # eval_global_per_round_num_interactions_until_success([Path(p) for p in sys.argv[1:]])
