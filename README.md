# mlops-test
Please implement a inference service of translation that runs on Kubernetes and provides a RESTful API on port 9527.

The translation model is `M2M100`, and the example can be found in `app/translation_example.py`.

You should first fork this repository and then create a PR when you're finished.


## Delivery
- **app/Dockerfile**: To generate an application image
- **k8s/deployment.yaml**: To deploy image to Kubernetes
- Other necessary code

## Input/Ouput

When you execute this command:
```bash
curl -X 'POST' \
  'http://127.0.0.1:9527/translation?text=Life%20is%20like%20a%20box%20of%20chocolates.&source_language=en&target_language=ja' \
  -H 'accept: application/json' \
  -d ''
```

Should return:
```bash
{
  "result": "人生はチョコレートの箱のようなものだ。"
}
```
