"""
Demo script for terminal recordings (GIFs).
Two modes:
  python demo.py train    - 300 iterations of gradient descent, prints progress
  python demo.py validate - loads pre-trained weights, prints per-character accuracy
"""
import sys
import math
import os

# ── shared helpers from project.py ──────────────────────────────────────────

def read_data(file_name, is_class=False):
    data_points = []
    with open(file_name, 'r') as f:
        for line in f.read().split('\n'):
            values = line.split(' ')
            try:
                row = [float(v) for v in values]
                row.append(1.0 if is_class else 0.0)
                data_points.append(row)
            except ValueError:
                continue
    return data_points

def read_data_points(path, label):
    data_points = read_data(f'{path}/{label}.txt', True)
    true_label_num = len(data_points)
    for item in os.listdir(path):
        if item == label + '.txt':
            continue
        data = read_data(f'{path}/{item}', False)
        if data:
            data_points.extend(data)
    return data_points, true_label_num

def calculate_p_y_1(data_point, w_list):
    score = w_list[0]
    for i in range(1, len(w_list)):
        score += w_list[i] * data_point[i - 1]
    return 1.0 / (1 + math.exp(-score))

def get_p_list(data_points, w_list):
    return [calculate_p_y_1(dp, w_list) for dp in data_points]

def calculate_acc(data_points, p_list):
    correct = sum(
        1 for i, p in enumerate(p_list)
        if (p >= 0.5) == bool(data_points[i][-1])
    )
    return float(correct) / len(p_list)

def get_total_der_w(data_points, w_list, p_list):
    total = [0.0] * len(w_list)
    for dp, p in zip(data_points, p_list):
        y = bool(dp[-1])
        for i in range(len(w_list)):
            h = 1 if i == 0 else dp[i - 1]
            total[i] += h * (y - p)
    return total

def load_w_list(label):
    path = f'w_list/w_list_{label}.txt'
    w_list = []
    with open(path, 'r') as f:
        for line in f.read().split('\n'):
            try:
                w_list.append(float(line))
            except ValueError:
                continue
    return w_list

# ── demo modes ───────────────────────────────────────────────────────────────

def demo_train():
    label = '6'
    MAX_ITER = 300
    PRINT_EVERY = 50
    step = 0.00005

    print(f"  Loading data for label '{label}' ...")
    data_points, true_label_num = read_data_points('data_points', label)
    print(f"  {len(data_points)} total samples  |  {true_label_num} positive ('{label}')\n")

    w_list = [0.0] * len(data_points[0])

    print(f"  Running gradient descent  (max {MAX_ITER} iterations, lr={step})")
    print(f"  {'Iter':>6}  {'Accuracy':>10}  {'True Positives':>16}")
    print(f"  {'----':>6}  {'--------':>10}  {'----------------':>16}")

    for it in range(1, MAX_ITER + 1):
        p_list = get_p_list(data_points, w_list)
        total_der_w = get_total_der_w(data_points, w_list, p_list)
        for i in range(len(w_list)):
            w_list[i] += step * total_der_w[i]

        if it % PRINT_EVERY == 0 or it == 1:
            acc = calculate_acc(data_points, p_list)
            tp = sum(1 for i, p in enumerate(p_list) if p >= 0.5 and data_points[i][-1] == 1)
            print(f"  {it:>6}  {acc:>9.2%}  {tp:>6}/{true_label_num:<6}")

    print(f"\n  Done. Final accuracy: {acc:.2%}  ({tp}/{true_label_num} true positives)")


def demo_validate():
    trained = [f.replace('accuracy_', '').replace('.txt', '')
               for f in os.listdir('w_list') if f.startswith('accuracy_')]
    trained.sort()

    print("  Loading pre-trained weights and computing validation accuracy ...\n")
    print(f"  {'Label':^7}  {'Accuracy':^10}  {'Correct / Total':^16}")
    print(f"  {'-----':^7}  {'--------':^10}  {'----------------':^16}")

    for label in trained:
        w_list = load_w_list(label)
        data_points, true_label_num = read_data_points('data_points', label)
        p_list = get_p_list(data_points, w_list)
        acc = calculate_acc(data_points, p_list)
        correct = int(acc * len(data_points))
        bar = '█' * int(acc * 20)
        print(f"  '{label:^5}'  {acc:>9.2%}  {correct:>6}/{len(data_points):<6}  {bar}")

    print(f"\n  {len(trained)} classifiers evaluated.")


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else ''
    if mode == 'train':
        print("\n╔══════════════════════════════════════╗")
        print("║   OCR — Training Demo  (label: '6')  ║")
        print("╚══════════════════════════════════════╝\n")
        demo_train()
    elif mode == 'validate':
        print("\n╔═══════════════════════════════════════╗")
        print("║   OCR — Validation Demo               ║")
        print("╚═══════════════════════════════════════╝\n")
        demo_validate()
    else:
        print("Usage: python demo.py [train|validate]")
