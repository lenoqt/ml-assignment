from modules.storage import Model
import pytest
import torch.nn as nn
from transformers import (
    AutoConfig,
    AutoModelForSequenceClassification,
    AutoTokenizer,
)


class NeuralNetwork(nn.Module):
    def __init__(self):
        super(NeuralNetwork, self).__init__()
        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(28*28, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, 10),
        )

    def forward(self, x):
        x = self.flatten(x)
        logits = self.linear_relu_stack(x)
        return logits

@pytest.fixture(autouse=True)
def simple_model():
    return NeuralNetwork()

@pytest.fixture
def simple_model_instance(simple_model):
    return Model(model=simple_model)

@pytest.fixture(autouse=True)
def pretrained_model():
    model_name = "distilbert-base-cased"
    config = AutoConfig.from_pretrained(
        model_name,
        num_labels=2,
        finetuning_tasl="mnli"
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, config=config)
    return model, tokenizer, config
    

def test_model_instance_no_tokenizer_no_config(simple_model):
    model = Model(model=simple_model)
    
    assert model.name 
    assert not model.tokenizer
    assert not model.config
    assert model.id

def test_model_pre_trained(pretrained_model):
    model, tokenizer, config = pretrained_model
    model = Model(model=model, tokenizer=tokenizer, config=config)

    assert model.name
    assert model.tokenizer
    assert model.config
    assert model.id

def test_upload_simple_model(simple_model_instance):
    simple_model_instance.upload_to_minio_s3()
    
    for _, uploaded in simple_model_instance._uploaded.items():
        assert uploaded

    simple_model_instance.delete_from_minio_s3()

def test_get_simple_model(simple_model_instance):
    model_id = str(simple_model_instance.id)
    simple_model_instance.upload_to_minio_s3()

    model_from_s3 = Model.from_minio_s3(model_id)

    assert isinstance(model_from_s3.model, nn.Module)

    simple_model_instance.delete_from_minio_s3()

def test_upload_pre_trained(pretrained_model):
    model, tokenizer, config = pretrained_model 
    pre_trained = Model(model=model, tokenizer=tokenizer, config=config)
    pre_trained.upload_to_minio_s3()
    
    for _, uploaded in pre_trained._uploaded.items():
        assert uploaded

    pre_trained.delete_from_minio_s3()
