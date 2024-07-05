## Incremental Learning of Humanoid Robot Behavior from Natural Interaction and Large Language Models

Abstract:

> Natural-language dialog is key for intuitive human-robot interaction. It can be used not only to express humans'
> intents, but also to communicate instructions for improvement if a robot does not understand a command correctly. Of
> great importance is to let robots learn from such interaction experience in an incremental way to allow them to improve
> their behaviors or avoid mistakes in the future. In this paper, we propose a system to achieve such incremental learning
> of complex behavior from natural interaction, and demonstrate its implementation on a humanoid robot. Our system deploys
> Large Language Models (LLMs) for high-level orchestration of the robot's behavior, based on the idea of enabling the LLM
> to generate Python statements in an interactive console to invoke both robot perception and action. Human instructions,
> environment observations, and execution results are fed back to the LLM, thus informing the generation of the next
> statement. Specifically, we introduce incremental learning from interaction, which enables the system to learn from its
> mistakes. For that purpose, the LLM can call another LLM responsible for code-level improvements of the current
> interaction based on human feedback. Subsequently, we store the improved interaction in the robot's memory so that it
> can later be retrieved on semantically similar requests. We integrate the system in the robot cognitive architecture of
> the humanoid robot ARMAR-6 and evaluate our methods both quantitatively (in simulation) and qualitatively (in simulation
> and real-world) by demonstrating generalized incrementally-learned knowledge.

For more details, see the [paper](https://arxiv.org/abs/2309.04316).

This repository contains the code to reproduce the simulated experiments from our paper. 
They are based on the experiments from
[Code as Policies](https://github.com/google-research/google-research/tree/master/code_as_policies).

To reproduce the experimental results:

1. Setup the virtual environment (Python 3.10) using `pip install -r requirements.txt`
2. `cd cap_simulation`
3. Download the files required for the simulation using `./download_files.sh`
4. In a separate terminal, run `python -m pybullet_utils.runServer` (this will keep running)
5. Make sure that the environment variable `OPENAI_API_KEY` is set appropriately
6. Run `PYTHONPATH=.. python -m setup`. Adapt `setup.py` to use different configuration files or change
   attributes/instructions seen/unseen.
7. Save the command's output to some file, e.g. `result.txt`. Extract the large json at the end of the file to another
   file `result.json`. Run `python calc_metrics.py result.json` to evaluate

