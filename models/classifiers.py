
import torch
from models.feature_extractors import get_feature_extractor_imagenet
from models.helpers import get_output_dim

def get_classifier_imagenet(architecture: str, num_classes: int) -> tuple:
    model, preprocess = get_feature_extractor_imagenet(architecture)

    output_dim = get_output_dim(model, preprocess)

    # defining the classifier with the appended linear layer
    class Classifier(torch.nn.Module):
        def __init__(self):
            super(Classifier).__init__()

            self.model = model
            self.fc = torch.nn.Linear(output_dim, num_classes, bias=False)
            
        def forward(self, x):
            return self.fc(self.model(x))

    return Classifier(), preprocess
