# enable_nbextensions    --> allow Plotly
# TagRemovePreprocessor  --> don't display cells tagged with 'hide' 
# file_whitelist         --> serve app.ipynb and robots.txt
# debug                  --> show error outputs

voila \
    --enable_nbextensions=True \
    --TagRemovePreprocessor.remove_cell_tags='{"hide"}' \
    --VoilaConfiguration.file_whitelist="['(app.ipynb)|(robots.txt)']" \
    --debug \
    app.ipynb