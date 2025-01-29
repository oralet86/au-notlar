import torch
from torchvision import transforms
from PIL import Image
import numpy as np
from torch.utils.data import Dataset
import os

_MODEL = None


class OCRModel(torch.nn.Module):
    def __init__(self):
        super(OCRModel, self).__init__()
        self.conv1 = torch.nn.Conv2d(1, 16, kernel_size=3, stride=1, padding=1)
        self.pool = torch.nn.MaxPool2d(2, 2)
        self.conv2 = torch.nn.Conv2d(16, 32, kernel_size=3, stride=1, padding=1)
        self.fc1 = torch.nn.Linear(32 * 6 * 5, 128)
        self.fc2 = torch.nn.Linear(128, 101)

    def forward(self, x):
        x = self.pool(torch.relu(self.conv1(x)))
        x = self.pool(torch.relu(self.conv2(x)))
        x = torch.flatten(x, start_dim=1)
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x


transform = transforms.Compose(
    [
        transforms.Resize((25, 20)),
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,)),
    ]
)


def load_model():
    _MODEL = OCRModel()
    _MODEL.load_state_dict(torch.load("ocr_model.pth", weights_only=True))
    _MODEL.eval()


def predict(image: np.ndarray):
    # If the model is not loaded, load it
    if _MODEL is None:
        load_model()
    # Load and preprocess the image
    image = Image.fromarray(image).convert("L")  # Convert to grayscale
    image = transform(image).unsqueeze(0)  # Add batch dimension

    # Run the model on the image
    with torch.no_grad():
        outputs = _MODEL(image)
        _, predicted_label = torch.max(outputs, 1)  # Get the index of the highest score

    return predicted_label.item()


class CaptchaImageDataset(Dataset):
    def __init__(self, root_dir: str, transform=None, target_transform=None):
        self.root_dir = root_dir
        self.images = [f for f in os.listdir(root_dir) if os.path.isfile(root_dir + f)]
        self.labels = [
            int(image_name[: image_name.find("_")]) for image_name in self.images
        ]
        self.classes = list(range(0, 101))
        self.transform = transform
        self.target_transform = target_transform

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        image_name: str = self.images[idx]
        image = Image.open(self.root_dir + image_name)
        label = self.labels[idx]
        if self.transform:
            image = self.transform(image)
        if self.target_transform:
            label = self.target_transform(label)
        return image, label


if __name__ == "__main__":
    ...
