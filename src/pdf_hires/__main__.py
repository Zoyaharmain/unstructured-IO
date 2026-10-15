import argparse
import json
from pathlib import Path
from . import extract_pdf


def main():
    parser = argparse.ArgumentParser(description='Original Unstructured PDF hi_res processing')
    parser.add_argument('pdf', type=Path)
    parser.add_argument('-o', '--output', type=Path)
    parser.add_argument('--model', default=None, help='Upstream model name; default: yolox or upstream environment override')
    parser.add_argument('--languages', nargs='+', default=['eng'])
    parser.add_argument('--dpi', type=int, default=None)
    parser.add_argument('--infer-table-structure', action='store_true')
    parser.add_argument('--settings', type=Path, help='JSON object of additional original PDF keyword settings')
    args = parser.parse_args()
    settings = json.loads(args.settings.read_text()) if args.settings else {}
    settings.update(languages=args.languages, hi_res_model_name=args.model,
                    infer_table_structure=args.infer_table_structure)
    if args.dpi is not None:
        settings['pdf_image_dpi'] = args.dpi
    result = extract_pdf(args.pdf, **settings)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(payload, encoding='utf-8')
    else:
        print(payload, end='')


if __name__ == '__main__':
    main()
