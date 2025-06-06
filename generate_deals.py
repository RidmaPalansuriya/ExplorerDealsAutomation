diff --git a//dev/null b/generate_deals.py
index 0000000000000000000000000000000000000000..90fd5a3fda1d02150bd23cac614a913f5ebc8d68 100644
--- a//dev/null
+++ b/generate_deals.py
@@ -0,0 +1,90 @@
+"""Generate clean deal listings from a CSV file.
+
+This script reads an input CSV containing two columns named ``RawTitle`` and
+``RawDescription``. It cleans each row and uses the OpenAI API to generate a
+catchy product title, an HTML-formatted description, and a short SEO
+description. The results are written to a new CSV file with additional columns
+``Formatted Title``, ``HTML Description`` and ``SEO Description``.
+
+Example usage:
+
+```
+python generate_deals.py input.csv output.csv --api-key YOUR_KEY
+```
+
+``OPENAI_API_KEY`` can be set in the environment instead of passing
+``--api-key``.
+"""
+
+import argparse
+import json
+import os
+
+import openai
+import pandas as pd
+
+
+def build_prompt(title: str, description: str) -> str:
+    """Create prompt requesting formatted deal output."""
+    return f"""
+You are helping prepare deal listings. Rewrite the following info
+into a catchy product title, a short HTML-formatted description (with
+<h2>, <ul>, <li>, and a few emojis if appropriate), and a 1–2 sentence SEO description.
+
+Deal Title: {title}
+Deal Description: {description}
+
+Respond in JSON with keys: title, html_description, seo_description.
+"""
+
+
+def generate_listing(row):
+    prompt = build_prompt(row["clean_title"], row["clean_desc"])
+    try:
+        response = openai.ChatCompletion.create(
+            model="gpt-4",
+            temperature=0.7,
+            messages=[{"role": "user", "content": prompt}]
+        )
+        return json.loads(response.choices[0].message.content.strip())
+    except Exception as exc:  # OpenAIError or JSON decode error
+        # Return empty values so the script can continue processing
+        return {
+            "title": row["clean_title"],
+            "html_description": row["clean_desc"],
+            "seo_description": "",
+            "error": str(exc),
+        }
+
+
+def main(input_csv: str, output_csv: str, api_key: str) -> None:
+    openai.api_key = api_key
+
+    df = pd.read_csv(input_csv)
+
+    # basic cleaning
+    df["clean_title"] = df["RawTitle"].astype(str).str.strip().str.title()
+    df["clean_desc"] = df["RawDescription"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
+
+    results = df.apply(generate_listing, axis=1, result_type="expand")
+
+    df["Formatted Title"] = results["title"]
+    df["HTML Description"] = results["html_description"]
+    df["SEO Description"] = results["seo_description"]
+
+    df.to_csv(output_csv, index=False)
+    print(f"Saved formatted deals to {output_csv}")
+
+
+if __name__ == "__main__":
+    parser = argparse.ArgumentParser(description="Generate formatted deal text using OpenAI")
+    parser.add_argument("input_csv", help="CSV file containing RawTitle and RawDescription columns")
+    parser.add_argument("output_csv", help="Destination CSV for output")
+    parser.add_argument("--api-key", dest="api_key", default=os.getenv("OPENAI_API_KEY"), help="OpenAI API key")
+
+    args = parser.parse_args()
+    if not args.api_key:
+        raise SystemExit("OpenAI API key required via --api-key or OPENAI_API_KEY env var")
+
+    main(args.input_csv, args.output_csv, args.api_key)
+
