# enable_nbextensions    --> allow Plotly
# TagRemovePreprocessor  --> don't display cells tagged with 'hide'  
voila app.ipynb --enable_nbextensions=True --TagRemovePreprocessor.remove_cell_tags='{"hide"}'