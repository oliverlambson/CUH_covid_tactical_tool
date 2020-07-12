# enable_nbextensions    --> allow Plotly
# TagRemovePreprocessor  --> don't display cells tagged with 'hide'  
# debug                  --> show error outputs
voila app.ipynb --enable_nbextensions=True --TagRemovePreprocessor.remove_cell_tags='{"hide"}' --debug