"""RUNFORM v3 pilot pipeline — one image in, JSON + 3D base out.

  Step 0/1: gemini-3.8-flash  (runner filter -> strict zone audit -> JSON)
  Step 2:   gemini-3-pro-image-preview (neutral 3D body base, NO markers/text;
            markers are overlaid deterministically from JSON in the HTML)

  Usage:
    python3 run_report.py reference/input/<photo>.jpg

  Outputs (under output/):
    step1_<name>.json, assets/body3d_<name>.png
    HTML report is rendered from the JSON (currently beach_report.html is the
    hand-tuned template for iteration; full JSON->HTML templating lands once
    the design is approved).

  Non-runner inputs stop at Step 0: {"is_running": false, ...}, no score.
"""
import io, json, os, sys
from PIL import Image
from google import genai

STEP1_MODEL = "gemini-3.8-flash"
STEP2_MODEL = "gemini-3-pro-image-preview"

STEP1_PROMPT = open(os.path.join(os.path.dirname(__file__), "step1_prompt.txt")).read() \
    if os.path.exists(os.path.join(os.path.dirname(__file__), "step1_prompt.txt")) \
    else None

BODY_PROMPT = ("Dark premium sports-science 3D render, Whoop/Oura app aesthetic. "
  "Two full-body translucent light-gray anatomically-neutral athletic mannequins "
  "on a pure black background: LEFT figure in side running profile (stance phase), "
  "RIGHT figure facing forward in athletic stance. Smooth matte clay render, soft rim "
  "lighting, featureless face, no clothing detail, no text, no labels, no markers, "
  "no dots, no lines, no numbers. Generous black padding, square composition.")

def _key():
    for line in open('/Users/sameerhoda/Projects/running_analysis/v2/.env'):
        if line.startswith('GEMINI_API_KEY='):
            return line.split('=', 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("GEMINI_API_KEY not found")

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else \
        'reference/input/depositphotos_97352806-stock-photo-runner-man-running-on-beach.jpg'
    name = os.path.splitext(os.path.basename(src))[0]
    client = genai.Client(api_key=_key())
    img = Image.open(src)

    r1 = client.models.generate_content(model=STEP1_MODEL, contents=[STEP1_PROMPT, img])
    text = r1.text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[1].rsplit('```', 1)[0]
    data = json.loads(text)
    os.makedirs('output/assets', exist_ok=True)
    with open(f'output/step1_{name}.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("step1:", json.dumps({k: data.get(k) for k in ('is_running', 'overall_score', 'camera_angle', 'gait_phase')}, indent=2))
    if not data.get('is_running'):
        print("Not a runner — stopping, no score.")
        return

    r2 = client.models.generate_content(model=STEP2_MODEL, contents=[BODY_PROMPT])
    for cand in r2.candidates:
        for part in cand.content.parts:
            if getattr(part, 'inline_data', None) and part.inline_data.data:
                out = Image.open(io.BytesIO(part.inline_data.data))
                out.save(f'output/assets/body3d_{name}.png')
                print(f"step2: saved output/assets/body3d_{name}.png {out.size}")
                return
    print("step2: WARNING — no image returned")

if __name__ == '__main__':
    main()
