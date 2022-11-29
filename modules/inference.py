from .storage import Model
import torch
import tempfile
from transformers import AutoModel

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MAX_NEW_TOKENS = 50

def get_translation_model(name: str) -> Model:
    return Model.from_pretrained(name)


model_obj = get_translation_model("facebook/m2m100_418M")


def infer_m2m100(input, target_lang):
    model_inputs = model_obj.tokenizer(input, return_tensors="pt").to(DEVICE)
    outputs = model_obj.model.generate(
        **model_inputs,
        max_new_tokens=MAX_NEW_TOKENS,
        forced_bos_token_id=model_obj.tokenizer.get_lang_id(target_lang)
    )
    return model_obj.tokenizer.batch_decode(outputs, skip_special_tokens=True)
