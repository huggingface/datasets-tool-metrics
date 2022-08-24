# Copyright 2021 The HuggingFace Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import argparse
import logging
from os import mkdir
from os.path import isdir
from pathlib import Path
import streamlit.components.v1 as components

import streamlit as st




#"""
#Examples:
## When not in deployment mode
#streamlit run app.py -- --live=False
#
## When deployed.
#streamlit run app.py
#"""

from data_measurements import dataset_statistics
from utils import dataset_utils
from utils import streamlit_utils as st_utils


logs = logging.getLogger(__name__)
logs.setLevel(logging.WARNING)
logs.propagate = False



st.set_page_config(
    page_title="Demo to showcase dataset metrics",
    page_icon="https://huggingface.co/front/assets/huggingface_logo.svg",
    layout="wide",
    initial_sidebar_state="auto",
)



 #with open('style.css') as f:
  #      st.markdown(f'<style>{f.read()}</style>',unsafe_allow_html=True)

if not logs.handlers:

    Path('./log_files').mkdir(exist_ok=True)

    # Logging info to log file
    file = logging.FileHandler("./log_files/app.log")
    fileformat = logging.Formatter("%(asctime)s:%(message)s")
    file.setLevel(logging.INFO)
    file.setFormatter(fileformat)

    # Logging debug messages to stream
    stream = logging.StreamHandler()
    streamformat = logging.Formatter("[data_measurements_tool] %(message)s")
    stream.setLevel(logging.WARNING)
    stream.setFormatter(streamformat)

    logs.addHandler(file)
    logs.addHandler(stream)



# colorblind-friendly colors
colors = [
    "#332288",
    "#117733",
    "#882255",
    "#AA4499",
    "#CC6677",
    "#44AA99",
    "#DDCC77",
    "#88CCEE",
]

CACHE_DIR = dataset_utils.CACHE_DIR
# String names we are using (not coming from the stored dataset).
OUR_TEXT_FIELD = dataset_utils.OUR_TEXT_FIELD
TOKENIZED_FIELD = dataset_utils.TOKENIZED_FIELD
EMBEDDING_FIELD = dataset_utils.EMBEDDING_FIELD
LENGTH_FIELD = dataset_utils.LENGTH_FIELD
# TODO: Allow users to specify this.
_MIN_VOCAB_COUNT = 10
_SHOW_TOP_N_WORDS = 10


@st.cache(
    hash_funcs={
        dataset_statistics.DatasetStatisticsCacheClass: lambda dstats: dstats.cache_path
    },
    allow_output_mutation=True,
)
def load_or_prepare(ds_args, show_embeddings, show_perplexities, use_cache=False):
    """
    Takes the dataset arguments from the GUI and uses them to load a dataset from the Hub or, if
    a cache for those arguments is available, to load it from the cache.
    Args:
        ds_args (dict): the dataset arguments defined via the streamlit app GUI
        show_embeddings (Bool): whether embeddings should we loaded and displayed for this dataset
        show_perplexities (Bool): whether perplexities should be loaded and displayed for this dataset
        use_cache (Bool) : whether the cache is used by default or not
    Returns:
        dstats: the computed dataset statistics (from the dataset_statistics class)
    """
    if not isdir(CACHE_DIR):
        logs.warning("Creating cache")
        # We need to preprocess everything.
        # This should eventually all go into a prepare_dataset CLI
        mkdir(CACHE_DIR)
    if use_cache:
        logs.warning("Using cache")
    dstats = dataset_statistics.DatasetStatisticsCacheClass(CACHE_DIR, **ds_args, use_cache=use_cache)
    logs.warning("Loading dataset")
    dstats.load_or_prepare_dataset()
    logs.warning("Loading labels")
    dstats.load_or_prepare_labels()
    logs.warning("Loading text lengths")
    dstats.load_or_prepare_text_lengths()
    logs.warning("Loading duplicates")
    dstats.load_or_prepare_text_duplicates()
    logs.warning("Loading vocabulary")
    dstats.load_or_prepare_vocab()
    logs.warning("Loading general statistics...")
    dstats.load_or_prepare_general_stats()
    if show_embeddings:
        logs.warning("Loading Embeddings")
        dstats.load_or_prepare_embeddings()
    if show_perplexities:
        logs.warning("Loading Text Perplexities")
        dstats.load_or_prepare_text_perplexities()
    logs.warning("Loading nPMI")
    try:
        dstats.load_or_prepare_npmi()
    except:
        logs.warning("Missing a cache for npmi")
    logs.warning("Loading Zipf")
    dstats.load_or_prepare_zipf()
    return dstats

@st.cache(
    hash_funcs={
        dataset_statistics.DatasetStatisticsCacheClass: lambda dstats: dstats.cache_path
    },
    allow_output_mutation=True,
)
def load_or_prepare_widgets(ds_args, show_embeddings, show_perplexities, live=False, use_cache=False):
    """
    Loader specifically for the widgets used in the app.
    Args:
        ds_args:
        show_embeddings:
        show_perplexities:
        use_cache:

    Returns:

    """

    if use_cache:
        logs.warning("Using cache")
    dstats = dataset_statistics.DatasetStatisticsCacheClass(CACHE_DIR, **ds_args, use_cache=use_cache)
    # Don't recalculate when we're live
    dstats.set_deployment(live)
    # checks whether the cache_dir exists in deployment mode
    # creates cache_dir if not and if in development mode
    cache_dir_exists = dstats.check_cache_dir()
    if cache_dir_exists:
        try:
            # We need to have the text_dset loaded for further load_or_prepare
            dstats.load_or_prepare_dataset()
        except:
            logs.warning("Missing a cache for load or prepare dataset")
        try:
            # Header widget
            dstats.load_or_prepare_dset_peek()
        except:
            logs.warning("Missing a cache for dset peek")
        try:
            dstats.load_or_prepare_vocab()
        except:
            logs.warning("Missing a cache for vocab.")
        try:
            # General stats widget
            dstats.load_or_prepare_general_stats()
        except:
            logs.warning("Missing a cache for general stats")
        try:
            # Labels widget
            dstats.load_or_prepare_labels()
        except:
            logs.warning("Missing a cache for prepare labels")
        try:
            # Text lengths widget
            dstats.load_or_prepare_text_lengths()
        except:
            logs.warning("Missing a cache for text lengths")
        if show_embeddings:
            try:
                # Embeddings widget
                dstats.load_or_prepare_embeddings()
            except:
                logs.warning("Missing a cache for embeddings")
        if show_perplexities:
            try:
                # Embeddings widget
                dstats.load_or_prepare_text_perplexities()
            except:
                logs.warning("Missing a cache for text perplexities")
        try:
            dstats.load_or_prepare_text_duplicates()
        except:
            logs.warning("Missing a cache for text duplicates")
        try:
            dstats.load_or_prepare_npmi()
        except:
            logs.warning("Missing a cache for npmi")
        try:
            dstats.load_or_prepare_zipf()
        except:
            logs.warning("Missing a cache for zipf")
    return dstats, cache_dir_exists

def show_column(dstats, ds_name_to_dict, show_embeddings, show_perplexities, column_id):
    """
    Function for displaying the elements in the right column of the streamlit app.
    Args:
        ds_name_to_dict (dict): the dataset name and options in dictionary form
        show_embeddings (Bool): whether embeddings should we loaded and displayed for this dataset
        show_perplexities (Bool): whether perplexities should be loaded and displayed for this dataset
        column_id (str): what column of the dataset the analysis is done on
    Returns:
        The function displays the information using the functions defined in the st_utils class.
    """
    # Note that at this point we assume we can use cache; default value is True.
    # start showing stuff

    #title_str = f"### Showing{column_id}: {dstats.dset_name} - {dstats.dset_config} - {dstats.split_name} - {'-'.join(dstats.text_field)}"
    #st.markdown(title_str)
    tab1, tab2, tab3, tab4, tab5, tab6, tab7,tab8 = st.tabs(["Dataset Description", "General Text Statistics", "Label Distribution", "Text Lengths","Text Duplicates","Text Perplexities","nPMI","Zipfs Law Fit"])#,"Text Embedding Clustering"])
    
    with tab1:
        logs.info("showing header")
        st_utils.expander_header(dstats, ds_name_to_dict, column_id)
    with tab2:
        logs.info("showing general stats")
        st_utils.expander_general_stats(dstats, column_id)
    with tab3:
        st_utils.expander_label_distribution(dstats.fig_labels, column_id)
    with tab4:
        st_utils.expander_text_lengths(dstats, column_id)
    with tab5:
        st_utils.expander_text_duplicates(dstats, column_id)
    with tab6:
        st_utils.expander_text_perplexities(dstats, column_id)
    # Uses an interaction; handled a bit differently than other widgets.
    with tab7:
        logs.info("showing npmi widget")
        st_utils.npmi_widget(dstats.npmi_stats, _MIN_VOCAB_COUNT, column_id)
    with tab8:
        logs.info("showing zipf")
        st_utils.expander_zipf(dstats.z, dstats.zipf_fig, column_id)
    #with tab9:
        #if show_embeddings:
        #    st_utils.expander_text_embeddings(
        #        dstats.text_dset,
        #        dstats.fig_tree,
        #        dstats.node_list,
        #        dstats.embeddings,
        #        OUR_TEXT_FIELD,
        #        column_id,
        #    )

    title_str = f"### Showing{column_id}: {dstats.dset_name} - {dstats.dset_config} - {dstats.split_name} - {'-'.join(dstats.text_field)}"
    st.markdown(title_str)
    logs.info("showing header")
    st_utils.expander_header(dstats, ds_name_to_dict, column_id)
    logs.info("showing general stats")
    st_utils.expander_general_stats(dstats, column_id)
    st_utils.expander_label_distribution(dstats.fig_labels, column_id)
    st_utils.expander_text_lengths(dstats, column_id)
    st_utils.expander_text_duplicates(dstats, column_id)
    # Uses an interaction; handled a bit differently than other widgets.
    logs.info("showing npmi widget")
    st_utils.npmi_widget(dstats.npmi_stats, _MIN_VOCAB_COUNT, column_id)
    logs.info("showing zipf")
    st_utils.expander_zipf(dstats.z, dstats.zipf_fig, column_id)
    if show_embeddings:
        st_utils.expander_text_embeddings(
            dstats.text_dset,
            dstats.fig_tree,
            dstats.node_list,
            dstats.embeddings,
            OUR_TEXT_FIELD,
            column_id,
        )
    if show_perplexities:
        st_utils.expander_text_perplexities(dstats, column_id)



def main():
    with open("style.css") as f:                                                # Reading style.css file and opening it 
        st.markdown(f'<style>{f.read()}</style>',unsafe_allow_html= True)       # Storing all styles in the streamlit markdown  &   unsafe_allow_html to true so that we can use html tags with the code  
    #----read and run html file

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live", default=False, required=False, action="store_true", help="Flag to specify that this is not running live.")
    arguments = parser.parse_args()
    live = arguments.live


    # Sidebar description and selection

    ds_name_to_dict = dataset_utils.get_dataset_info_dicts()
    st.title("Data Measurements Tool")
    st.markdown("""
    This demo showcases the [dataset metrics as we develop them](https://huggingface.co/blog/data-measurements-tool).
    
    With this tool, you can:
    
    ✓ Dynamic loading of datasets in the lib

    ✓ Fetching config and info without downloading the dataset

    ✓ Propose the list of candidate text and label features to select
    We are still working on:

    ✓ Implementing all the current tools
    """,
        unsafe_allow_html=True,)
    # Get the sidebar details
    st_utils.sidebar_header()
    # Set up naming, configs, and cache path.
    #compare_mode = st.sidebar.checkbox("Comparison mode")

    # When not doing new development, use the cache.
    use_cache = True

    #show_embeddings = 0 #st.sidebar.checkbox("Show text clusters")
    # List of datasets for which embeddings are hard to compute:

    
    show_embeddings =0 #st.sidebar.checkbox("Show text clusters")
    show_perplexities =0# st.sidebar.checkbox("Show text perplexities")
  
    logs.warning("Using Single Dataset Mode")
    dataset_args = st_utils.sidebar_selection(ds_name_to_dict, "")
    dstats, cache_exists = load_or_prepare_widgets(dataset_args, show_embeddings,show_perplexities, live=live, use_cache=use_cache)
    if cache_exists:
        show_column(dstats, ds_name_to_dict, show_embeddings, show_perplexities, "")
    else:

        st.markdown("### Missing pre-computed data measures!")
        st.write(dataset_args)
    
    st.sidebar.write('\n')
    st.sidebar.write('\n')
    st.sidebar.write('\n')
    #st.sidebar.write('\n')

    ### this is in streamlit_utils.py
    #st.sidebar.markdown(
   #     """
    
   # The tool is in development, and will keep growing in utility and functionality 🤗🚀
   # """,
   #     unsafe_allow_html=True,
   # )

    logs.warning("Using Single Dataset Mode")
    dataset_args = st_utils.sidebar_selection(ds_name_to_dict, "")
    dstats, cache_exists = load_or_prepare_widgets(dataset_args, show_embeddings, show_perplexities, live=live, use_cache=use_cache)
    if cache_exists:
        show_column(dstats, ds_name_to_dict, show_embeddings, show_perplexities, "")
    else:
        st.markdown("### Missing pre-computed data measures!")
        st.write(dataset_args)

    


    # List of datasets for which embeddings are hard to compute:

    if compare_mode:
        logs.warning("Using Comparison Mode")
        dataset_args_left = st_utils.sidebar_selection(ds_name_to_dict, " A")
        dataset_args_right = st_utils.sidebar_selection(ds_name_to_dict, " B")
        left_col, _, right_col = st.columns([10, 1, 10])
        dstats_left, cache_exists_left = load_or_prepare_widgets(
            dataset_args_left, show_embeddings, show_perplexities, live=live, use_cache=use_cache
        )
        with left_col:
            if cache_exists_left:
                show_column(dstats_left, ds_name_to_dict, show_embeddings, show_perplexities," A")
            else:
                st.markdown("### Missing pre-computed data measures!")
                st.write(dataset_args_left)
        dstats_right, cache_exists_right = load_or_prepare_widgets(
            dataset_args_right, show_embeddings, show_perplexities, live=live, use_cache=use_cache
        )
        with right_col:
            if cache_exists_right:
                show_column(dstats_right, ds_name_to_dict, show_embeddings, show_perplexities, " B")
            else:
                st.markdown("### Missing pre-computed data measures!")
                st.write(dataset_args_right)
    else:
        logs.warning("Using Single Dataset Mode")
        dataset_args = st_utils.sidebar_selection(ds_name_to_dict, "")
        dstats, cache_exists = load_or_prepare_widgets(dataset_args, show_embeddings, show_perplexities, live=live, use_cache=use_cache)
        if cache_exists:
            show_column(dstats, ds_name_to_dict, show_embeddings, show_perplexities, " A")
        else:
            st.markdown("### Missing pre-computed data measures!")
            st.write(dataset_args)



if __name__ == "__main__":
    main()