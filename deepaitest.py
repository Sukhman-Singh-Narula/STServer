import requests

# Replace this with your actual DeepAI API key
API_KEY = 'your_deepai_api_key'

def generate_image(prompt):
    url = "https://api.deepai.org/api/text2img"
    
    response = requests.post(
        url,
        data={'text': prompt},
        headers={'api-key': API_KEY}
    )

    if response.status_code == 200:
        output_url = response.json()['output_url']
        print(f"✅ Image generated: {output_url}")
        return output_url
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        return None

# Example usage
generate_image("A futuristic robot teddy bear playing in a park")
