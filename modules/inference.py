from .storage import Model


def get_translation_model(name: str) -> Model:
    return Model.from_pretrained(name)


model = get_translation_model("facebook/m2m100_418M")


def infer_m2m100(input, target_lang):

    model_inputs = model.tokenizer(input, return_tensors="pt")
    outputs = model.model.generate(
        **model_inputs, forced_bos_token_id=model.tokenizer.get_lang_id(target_lang)
    )
    return model.tokenizer.batch_decode(outputs, skip_special_tokens=True)
