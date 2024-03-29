
import hydra
import copy
import wandb
from omegaconf import DictConfig
import lightning.pytorch as pl
from collections import defaultdict
from torchvision import transforms
from src.datasets.datasets import get_dataset_class_by_name
# TODO
from src.models.classifiers import \
    get_classifier_imagenet, get_classifier_imagenet_preprocess_only, get_classifier_from_simclr, get_classifier_simclr_preprocess_only
from src.datasets.subsets import get_n_random
from src.models.training import train_image_classifier
from src.utils.wandb import init_run, cast_dict_to_int

@hydra.main(version_base=None, config_path='../../conf', config_name='random_baseline')
def main(cfg: DictConfig):
    init_run(cfg)

    # we don't want this due to different sampling each time
    # pl.seed_everything(cfg.training.seed)

    preprocess = None
    if cfg.training.weights.type == 'imagenet':
        preprocess = get_classifier_imagenet_preprocess_only(cfg)
    elif cfg.training.weights.type == 'simclr':
        preprocess = get_classifier_simclr_preprocess_only(cfg)
    else:
        raise ValueError(f'unknown weights type: {cfg.training.weights.type}')

    dataset_class = get_dataset_class_by_name(cfg.dataset.name)

    # TODO: maybe add more
    transform = transforms.Compose([
        transforms.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.2, hue=0.05),
        transforms.RandomRotation(degrees=15),
    ])
    train_dataset = dataset_class('train', transform=transform, preprocess=preprocess)
    val_dataset = dataset_class('test', preprocess=preprocess)

    train_subset = get_n_random(train_dataset, cfg.training.train_samples)
    
    train_subset.reassign_classes()
    label_counts = defaultdict(int)
    for i in range(len(train_subset)):
        label_counts[train_subset[i]['label']] += 1
    wandb.config.labels = train_subset.get_number_of_labels()
    wandb.config.labels_text = train_subset.labels_text
    wandb.config.label_counts = cast_dict_to_int(label_counts)
    wandb.config.label_to_class_mapping = cast_dict_to_int(train_subset.label_to_class_mapping)
    wandb.config.class_to_label_mapping = cast_dict_to_int(train_subset.class_to_label_mapping)
    wandb.config.classes = train_subset.get_number_of_classes()

    val_subset = copy.deepcopy(val_dataset)
    val_subset.match_classes_and_filter(train_subset)

    num_classes = train_subset.get_number_of_classes()

    model = None
    if cfg.training.weights.type == 'imagenet':
        # TODO: add weight freezing option
        model, _ = get_classifier_imagenet(cfg, num_classes)
    elif cfg.training.weights.type == 'simclr':
        # TODO
        model = get_classifier_from_simclr(preprocess, cfg, num_classes)
    else:
        raise ValueError(f'unknown weights type: {cfg.training.weights.type}')

    train_image_classifier(model, train_subset, val_subset, cfg)

    wandb.finish()

if __name__ == '__main__':
    main()
