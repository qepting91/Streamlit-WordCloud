import streamlit as st
import requests
from bs4 import BeautifulSoup
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import numpy as np
from PIL import Image
import re
import matplotlib.pyplot as plt
from io import BytesIO
import base64

st.set_option('deprecation.showPyplotGlobalUse', False)

# Streamlit interface setup
st.title("Advanced Word Cloud Generator")
st.caption("Generate beautiful word clouds from any website.")

# Initialize session state variables
if 'url' not in st.session_state:
    st.session_state.url = ''

if 'scraped_text' not in st.session_state:
    st.session_state.scraped_text = ''
    
# Initialize a full_reset flag in session state
if 'image_uploaded' not in st.session_state:
    st.session_state.image_uploaded = False

def reset_state():
    for key in st.session_state.keys():
        if key in ['url', 'scraped_text', 'image_uploaded']:
            del st.session_state[key]
    
def is_valid_url(url):
    """ Validate the URL format. """
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'\S+$',  # non-whitespace characters
        re.IGNORECASE)
    return re.match(regex, url) is not None

@st.cache_data
def scrape_website(url):
    """ Scrape website content with error handling and user-agent header. """
    if not st.session_state.scraped_text or st.session_state.url != url:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            st.session_state.scraped_text = soup.get_text()  # Cache scraped text in session state
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to retrieve data from URL: {e}")
            return None
    return st.session_state.scraped_text

def get_image_download_link(img, filename, text):
    """Generates a link allowing the PIL image to be downloaded"""
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:file/png;base64,{img_str}" download="{filename}">{text}</a>'
    return href

def cloud(image, text, max_word, max_font, random):
    stopwords = set(STOPWORDS)
    stopwords.update(['us', 'one', 'will', 'said', 'now', 'well', 'man', 'may',
    'little', 'say', 'must', 'way', 'long', 'yet', 'mean',
    'put', 'seem', 'asked', 'made', 'half', 'much',
    'certainly', 'might', 'came'])
    
    wc = WordCloud(background_color="white", colormap="hot", max_words=max_word, mask=image,
    stopwords=stopwords, max_font_size=max_font, random_state=random)

    # Generate word cloud
    wc.generate(text)

    # Create coloring from image
    image_colors = ImageColorGenerator(image)

    # Create a figure with two subplots
    fig, axes = plt.subplots(1, 2, gridspec_kw={'width_ratios': [3, 2]})
    axes[0].imshow(wc.recolor(color_func=image_colors), interpolation="bilinear")
    axes[0].set_title('Word Cloud', fontsize=24)
    axes[0].axis('off')

    # Display the original image in the second subplot
    axes[1].imshow(image, cmap=plt.cm.gray, interpolation="bilinear")
    axes[1].set_title('Original Image', fontsize=24)
    axes[1].axis('off')

    # Show the figure with Streamlit
    st.pyplot(fig)

    # Provide download link for word cloud
    wordcloud_image = wc.to_array()
    wordcloud_image_pil = Image.fromarray(wordcloud_image)
    filename = "wordcloud.png"
    st.markdown(get_image_download_link(wordcloud_image_pil, filename, 'Download Word Cloud as Image'), unsafe_allow_html=True)

with st.sidebar:
    st.info("🎛️ Control Panel - Adjust the settings and provide inputs here.")
    max_word = st.slider("Max words", 200, 3000, 200)
    max_font = st.slider("Max Font Size", 50, 350, 60)
    random = st.slider("Random State", 30, 100, 42)
    image = st.file_uploader("Choose a file (preferably a silhouette)", key='image')
    url = st.text_input("Enter URL to scrape", value=st.session_state.url, key='url')
    submit_url = st.button("Scrape URL", key='submit_url')

    if submit_url:
        if st.session_state.url and is_valid_url(st.session_state.url):  # Use st.session_state.url directly
            scraped_text = scrape_website(st.session_state.url)  # Scrape and store the text
            if scraped_text:
                st.session_state.scraped_text = scraped_text  # Update scraped_text in session state
                st.success("Text successfully scraped! You can now generate the word cloud.")
            else:
                st.error("Failed to scrape the text. Please check the URL and try again.")
        elif not st.session_state.url:
            st.warning("Please enter a URL to proceed.")
        elif not is_valid_url(st.session_state.url):
            st.error("Invalid URL. Please enter a valid URL.")
    # Reset functionality for new text
    if st.sidebar.button("For New Text", key='new_text'):
        st.session_state.scraped_text = ''
        st.rerun()

    # Full Reset functionality
    if st.sidebar.button("Full Reset", key='full_reset'):
        reset_state()
        st.rerun()# Rerun the app to reset everything

# Main functionality
def main():
    st.info("ℹ️ Enter your image and URL in the control panel to get started. Modify the sliders to adjust the appearance of your word cloud.")
    generate_wordcloud = st.button("Generate Wordcloud", key='generate_wordcloud')
    if generate_wordcloud:
        if st.session_state.scraped_text and image:
            image_np = np.array(Image.open(image))
            cloud(image_np, st.session_state.scraped_text, max_word, max_font, random)
        else:
            if not st.session_state.scraped_text:
                st.error("Please scrape a URL for text before generating the word cloud.")
            if not image:
                st.error("Please upload an image to use as a mask for the word cloud.")

if __name__=="__main__":
    main()
