import torch
import ocr.ocr as o
from global_variables import TEST_DATA_FOLDER
from torch.utils.data import DataLoader
import time
import argparse
from sklearn.metrics import classification_report
import matplotlib.pyplot as plt


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load test dataset
testDataset = o.CaptchaImageDataset(root_dir=TEST_DATA_FOLDER, transform=o.transform)
# Create a DataLoader
testDataLoader = DataLoader(testDataset, batch_size=64, shuffle=False)

# Define loss function
lossFn = torch.nn.CrossEntropyLoss()


def load_models(*model_paths):
    models = {}
    for i, path in enumerate(model_paths[0]):
        model = torch.load(path).to(device)
        model.eval()
        models[f"Model {i+1}"] = model
    return models


def evaluate_model(model, dataLoader, device):
    total_loss = 0
    all_preds = []
    all_labels = []
    correct = 0
    total = 0

    # Measure inference time
    start_time = time.time()

    with torch.no_grad():
        for x, y in dataLoader:
            x, y = x.to(device), y.to(device)
            pred = model(x)

            loss = lossFn(pred, y)
            total_loss += loss.item()

            preds = pred.argmax(dim=1).cpu().numpy()
            labels = y.cpu().numpy()

            all_preds.extend(preds)
            all_labels.extend(labels)

            correct += (preds == labels).sum()
            total += len(labels)

    end_time = time.time()
    avg_loss = total_loss / len(dataLoader)
    accuracy = correct / total
    inference_time = end_time - start_time

    # Generate classification report
    class_report = classification_report(all_labels, all_preds, output_dict=True)

    return avg_loss, accuracy, inference_time, class_report


def compare_models(*model_paths):
    models = load_models(*model_paths)
    results = {}

    for name, model in models.items():
        loss, acc, time, report = evaluate_model(model, testDataLoader, device)
        results[name] = {"loss": loss, "accuracy": acc, "time": time, "report": report}

    # Print comparison results
    for name, result in results.items():
        print(
            f"{name} - Loss: {result['loss']:.4f}, Accuracy: {result['accuracy']:.4f}, Time: {result['time']:.2f}s"
        )

    model_names = list(results.keys())
    accuracy = [results[m]["accuracy"] for m in model_names]
    loss = [results[m]["loss"] for m in model_names]

    plt.figure(figsize=(10, 5))

    # Accuracy Bar Chart
    plt.subplot(1, 2, 1)
    plt.bar(
        model_names,
        accuracy,
        color=["blue", "green", "orange", "purple", "red"][: len(model_names)],
    )
    plt.title("Model Accuracy Comparison")
    plt.ylabel("Accuracy")

    # Loss Bar Chart
    plt.subplot(1, 2, 2)
    plt.bar(
        model_names,
        loss,
        color=["red", "purple", "yellow", "cyan", "magenta"][: len(model_names)],
    )
    plt.title("Model Loss Comparison")
    plt.ylabel("Loss")

    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare multiple OCR models.")
    parser.add_argument("models", nargs="+", help="Paths to model files")
    args = parser.parse_args()

    compare_models(args.models)
