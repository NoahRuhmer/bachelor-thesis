# Disclaimer: This code is part of the bachelor Thesis Dynamic Programming vs. Reinforcement Learning
# by Noah Ruhmer and supervised by Univ.-Prof. Dipl.-Ing. Dr.techn. Thomas Pock

# The following code is used to solve the Parking problem by a stochastic dynamic programming approach and by Q-learning

# Usage: The graphics generated in the thesis were generated by using the following functions

# Q_learn_and_plot(...)
# executes the q learning algorithm on given parameters of the parking problems and generates a plot
# demonstrating the learning curve over the iterations

# Q_learn_statistic(...)
# To generate statistical results to compare the approximated solution to the exact dynamic programming solution this
# function generates statistical results for the q learning results

# dp_plot_policy(...)
# executes the dp algorithm and plots the cost by policy and gives the optimal problem solution

import numpy as np
import matplotlib.pyplot as plt
import random

figure_path = "../bac-thesis/figures/code_statistics/"


def gen_spaces_binomial(n, probability_free):
    ret = np.random.choice([0, 1], size=n, p=[probability_free, 1 - probability_free])
    ret[-1] = 0
    return ret


def index_from_policy(n, spaces, policy):
    for index in range(policy, n):
        if not spaces[index]:
            return index
    return n - 1


def cost_from_index(n, index):
    if index == n - 1:
        return n / 2
    else:
        return n - index


def sample_policy(n, probability_free, policy, sample_count):
    parking_indices = []
    costs = []
    for i in range(sample_count):
        spaces = gen_spaces_binomial(n, probability_free)
        index = index_from_policy(n, spaces, policy)
        costs.append(cost_from_index(n, index))
        parking_indices.append(index)
    return [parking_indices, costs]


def try_different_strategies(n, probability_free, start_policy, end_policy, sample_count):
    avg_indices = []
    avg_costs = []
    garage_counts = []
    for strategy in range(start_policy, end_policy):
        i, c = sample_policy(n, probability_free, strategy, sample_count)
        avg_indices.append(np.average(i))
        avg_costs.append(np.average(c))
        garage_counts.append(i.count(n))
    return avg_indices, avg_costs, garage_counts


def plot_strategies(n, probability_free, start_strategy, end_strategy, file_ending, sample_count=1000):
    avg_indices, avg_costs, garage_counts = try_different_strategies(
        n, probability_free, start_strategy, end_strategy, sample_count)
    x = range(start_strategy, end_strategy)
    plt.plot(x, avg_indices, label="Average Parking Index")
    plt.plot(x, avg_costs, label="Average Cost")
    plt.xlabel('Index-threshold of the policy')
    plt.ylabel('Expected Cost')
    plt.title(f'Estimated Policy and Cost, N = {n}')
    plt.legend()
    plt.savefig(f"{figure_path}strategy_{file_ending}")
    plt.show()
    print(f"N = {n}\nOptimal average cost: {min(avg_costs)}\n")


def plot_probabilities(n, probabilities, start_strategy, end_strategy, file_ending, sample_count=1000):
    plt.title(f'Expected Cost for Policy and Probability, N = {n}')
    for probability in probabilities:
        avg_indices, avg_costs, garage_counts = try_different_strategies(
            n, probability, start_strategy, end_strategy, sample_count)
        x = range(start_strategy, end_strategy)
        plt.plot(x, avg_costs, label=f"p = {probability}")
        plt.xlabel('Index-threshold of the policy')
        plt.ylabel('Expected Cost')
        plt.legend()
    plt.savefig(f"{figure_path}strategy_{file_ending}")
    plt.show()


def generate_Q(n):
    return np.zeros((n + 1, 2))


# reward from original cost function: -cost + n
def standard_reward(n, state, next_state):
    if state == n - 1:
        return n / 2
    if next_state == n:
        return state + 1
    return 0


# DO NOT use this function, unreliable due to negative q-values
# def negated_cost(n, state, next_state):
#     if state == n - 1:
#         return -n / 2
#     if next_state == n:
#         return state + 1 - n
#    return 0


# Incremental reward function, slower but stable: -cost but reward given incrementally
def incremental_reward(n, state, next_state):
    if state == n - 1:
        return -n / 2
    if next_state == n:
        return 0
    return 1


def update_Q_table(n, Q, state, action, next_state, reward_function, learning_rate, discount_factor):
    Q[state, action] = Q[state, action] + learning_rate * \
                       (reward_function(n, state, next_state) + discount_factor * np.max(Q[next_state]) - Q[
                           state, action])


def training_episode(n, probability_free, Q, reward_function, learning_rate, exploration_rate, discount_factor):
    spaces = gen_spaces_binomial(n, probability_free)
    for k in range(0, n):
        if exploration_rate > random.uniform(0, 1):
            action = random.randint(0, 1)
        else:
            if Q[k, 0] == Q[k, 1]:  # solve ties randomly
                action = np.random.choice([0, 1], p=[0.5, 0.5])
            else:
                action = 1 if Q[k, 0] < Q[k, 1] else 0
        if action == 1 and spaces[k] == 0:
            next_state = n
        elif k == n - 1:
            next_state = n
        else:
            next_state = k + 1
        update_Q_table(n, Q, k, action, next_state, reward_function, learning_rate, discount_factor)
        if next_state == n:
            break
    return Q


def execute_Q_policy(n, probability_free, Q):
    spaces = gen_spaces_binomial(n, probability_free)
    parking_index = n - 1
    for k in range(0, n):
        if Q[k, 0] < Q[k, 1] and spaces[k] == 0:
            parking_index = k
            break
    return parking_index, cost_from_index(n, parking_index)


def q_learn(n, probability_free, Q, reward_function, learning_rate, exploration_rate, discount_factor, cycle_count,
            cycle_episodes, sample_size_for_mean=1000):
    avg_indices = []
    avg_costs = []
    max_episodes = cycle_count * cycle_episodes
    for cycle in range(0, cycle_count):
        for episode in range(0, cycle_episodes):
            current_learning_rate = learning_rate * (
                    max_episodes - cycle * cycle_episodes + episode + 1) / max_episodes
            current_exploration_rate = exploration_rate * (
                    max_episodes - cycle * cycle_episodes + episode + 1) / max_episodes
            Q = training_episode(n, probability_free, Q, reward_function, current_learning_rate,
                                 current_exploration_rate,
                                 discount_factor)
        indices = []
        costs = []
        for episode in range(0, sample_size_for_mean):
            index, cost = execute_Q_policy(n, probability_free, Q)
            indices.append(index)
            costs.append(cost)
        avg_indices.append(np.average(indices))
        avg_costs.append(np.average(costs))
    return Q, avg_indices, avg_costs


def plot_learning_curve(n, probaility_free, reward_function, avg_indices, avg_costs, filename_ending, cycle_count,
                        cycle_episodes):
    print(f"N = {n}")
    print(f"final avg_index: {avg_indices[-1]}")
    x = range(0, cycle_count)
    x = [element * cycle_episodes for element in x]

    # plt.plot(x, avg_indices, label="Average parking index")
    plt.plot(x, avg_costs)
    plt.xlabel('Training Iterations')
    plt.ylabel('Expected Cost')
    plt.title(f'Training progress, N = {n}, p = {probaility_free}, reward = {reward_function.__name__}')
    plt.axhline(avg_costs[-1], label=f"resulting cost = {round(avg_costs[-1], 3)}", color='red', alpha=0.8,
                xmin=0.05, xmax=0.95)
    plt.legend()
    plt.savefig(figure_path + "q_training_progress_" + filename_ending)
    plt.show()

    print(f"final avg_cost: {avg_costs[-1]}\n")


def Q_learn_statistic(n, probability_free, reward_function, learning_rate, exploration_rate, discount_factor,
                      cycle_count,
                      cycle_episodes, samples_per_avg, k):
    result_cost = []
    for i in range(k):
        Q = generate_Q(n)
        Q, avg_indices, avg_costs = q_learn(n, probability_free, Q, reward_function, learning_rate, exploration_rate,
                                            discount_factor, cycle_count, cycle_episodes, samples_per_avg)
        result_cost.append(avg_costs[-1])

    mean = np.average(result_cost)
    std = np.std(result_cost)
    print(f"N: {n}, p = {probability_free}, Mean: {mean}, Std: {std} from {k} samples\n")


def Q_learn_and_plot(n, probability_free, reward_function, learning_rate, exploration_rate, discount_factor, cycle_count,
                     cycle_episodes, samples_per_avg, filename_ending):
    Q = generate_Q(n)
    Q, avg_indices, avg_costs = q_learn(n, probability_free, Q, reward_function, learning_rate, exploration_rate,
                                        discount_factor, cycle_count, cycle_episodes, samples_per_avg)
    plot_learning_curve(n, probability_free, reward_function, avg_indices, avg_costs, filename_ending, cycle_count,
                        cycle_episodes)


def fun_rec(i, n, probability_free):
    if i == n:
        return n / 2
    return fun_rec(i + 1, n, probability_free) * (1 - probability_free) + (n - i) * probability_free


def fun_sum(i, n, probability_free):
    sum = n / 2 * (1 - probability_free) ** (n - i)
    for j in range(0, n - i):
        sum += probability_free * (n - i - j) * (1 - probability_free) ** (j)
    return sum


def dp_plot_policy(n, probability_free):
    for probability in probability_free:

        arr_sum = []
        for i in range(0, n + 1):
            arr_sum.append(fun_sum(i, n, probability))

        print(f"N = {n}, p = {probability}")
        print(f"optimal cost: {min(arr_sum)}")
        print(f"optimal policy is stopping at index: {np.argmin(arr_sum)}\n")

        x = range(0, n + 1)
        plt.plot(x, arr_sum, label=f"p = {probability}, opt. policy: {np.argmin(arr_sum)}")
        plt.plot(np.argmin(arr_sum), min(arr_sum), "bo")
        plt.ylabel('Cost')
        plt.xlabel('Index-threshold of the policy')
    plt.title(f'Cost for Policy and Probability, N = {n}')
    plt.legend()
    plt.savefig(f"{figure_path}strategy_probabilities_{n}")
    plt.show()


n = 200
alpha = 0.05
epsilon = 0.05
gamma = 0.999
episodes_per_cycle = 600
cycles = 100
samples = 10000
p = 0.05

Q_learn_and_plot(n, p, incremental_reward, alpha, epsilon, gamma, cycles, episodes_per_cycle, samples, "200")
Q_learn_statistic(n, p, incremental_reward, alpha, epsilon, gamma, cycles, episodes_per_cycle, samples, 20)
dp_plot_policy(n, [0.000000001, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1])
