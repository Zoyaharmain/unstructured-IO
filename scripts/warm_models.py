"""Prepare the installed library's own assets before serving requests."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--hi-res', action='store_true', help='Also cache the YOLOX layout model')
    parser.add_argument('--sections', action='store_true', help='Cache the pinned Sentence-BERT section encoder')
    args = parser.parse_args()
    from unstructured.nlp.tokenize import _get_nlp
    _get_nlp()
    if args.hi_res:
        from unstructured_inference.models.base import get_model
        get_model('yolox')
    if args.sections:
        # Importing the app is unnecessary during image construction.
        from sentence_transformers import SentenceTransformer
        config = json.loads((Path(__file__).resolve().parents[1] / 'local_api/data/section_model.json').read_text())
        SentenceTransformer(config['model_id'], revision=config['revision'], device='cpu', trust_remote_code=False)
    print('Local extraction and requested section model assets are ready.')


if __name__ == '__main__':
    main()
