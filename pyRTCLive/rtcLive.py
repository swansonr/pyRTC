#######################
# Import libraries
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from pyRTC import initExistingShm
from mpl_toolkits.axes_grid1 import make_axes_locatable

#######################
# Page configuration
st.set_page_config(
    page_title="pyRTC Live View",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded")

# alt.theme.enable("light")

#######################
# CSS styling
st.markdown("""
<style>

[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

[data-testid="stMetric"] {
    background-color: #393939;
    text-align: center;
    padding: 15px 0;
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

</style>
""", unsafe_allow_html=True)

#######################
# Load data
# df_reshaped = pd.read_csv('data/us-population-2010-2019-reshaped.csv')

color_theme_list = ['Blues', 'Cividis', 'Greens', 'Inferno', 'magma', 'plasma', 'Reds', 'rainbow', 'turbo', 'viridis']

# data_time_series = np.random.rand(1000, 4)
# data_wfs_data = np.random.rand(64, 32)

if 'shm_dict' not in st.session_state:
    slope_shm, slope_dshape, slope_dtype = initExistingShm("signal2D")

    st.session_state.shm_dict = {
        'signal2D': {
            'shm': slope_shm,
            'dshape': slope_dshape,
            'dtype': slope_dtype,
        },
    }

#######################
# Plot Devices

def make_line_plot(input_data, label_x, label_y, label_t, input_color):
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(input_data)
    ax.set_xlabel(label_x)
    ax.set_ylabel(label_y)
    ax.set_title(label_t)
    plt.set_cmap(input_color)

    return fig

def make_slope_plot(fig, ax, graph, input_data, vmin=None, vmax=None, norm=None):

    dx = input_data.shape[-2] // 2

    if not fig:
        fig, ax = plt.subplots(1, 2, dpi=800, figsize=(8, 12))

        graph = []
        graph.append(ax[0].imshow(input_data[:dx, :], vmin=vmin, vmax=vmax, norm=norm, cmap=st.session_state.selected_color_theme))
        graph.append(ax[1].imshow(input_data[dx:, :], vmin=vmin, vmax=vmax, norm=norm, cmap=st.session_state.selected_color_theme))

        ax[0].set_xlabel('x slopes')
        ax[1].set_xlabel('y slopes')
    else:
        graph[0].set_data(input_data[:dx, :])
        graph[1].set_data(input_data[dx:, :])

    return fig, ax, graph

def get_new_2D_values_list():
    updated_list = st.session_state['shm_2D_update'] #list
    current_list = st.session_state.shm_dict.copy()
    
    # remove shms
    for key, d in current_list.items():
        if key not in updated_list:     
            try:
                del st.session_state.shm_dict[key]
            except:
                st.write(f'Unable to delete SHM: {key}')

    # add shms
    for key in updated_list:
        if key not in current_list.keys():
            try:
                _shm, _dshape, _dtype = initExistingShm(key)

                st.session_state.shm_dict = {
                    key: {
                        'shm': _shm,
                        'dshape': _dshape,
                        'dtype': _dtype,
                    },
                }
            except:
                st.write(f'Unable to Open SHM: {key}')


# def get_new_1D_values_list():
#     st.write(st.session_state['shm_1D_update'])
    
# try:
#     loop = asyncio.get_running_loop()
# except RuntimeError:
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)

def main():
    #######################
    # Sidebar
    with st.sidebar:
        st.title('pyRTC Dashboard')

        # shm_options_2D = 
        st.multiselect(
            "2D SHMs to Visualize:",
            default = ["signal2D"],
            options = ["psfShort", "psfLong", "signal2D", "wfc2D", "wfs", "pol"],
            accept_new_options = True,
            on_change = get_new_2D_values_list,
            key = 'shm_2D_update',
        )

        # shm_options_1D = st.multiselect(
        #     "Scalar SHMs to Visualize:",
        #     default = ["strehl"],
        #     options = ["strehl"],
        #     accept_new_options = True,
        #     on_change=get_new_1D_values_list,
        #     key='shm_1D_update',
        # )

        st.session_state.selected_color_theme = st.selectbox('Color Theme', color_theme_list)

        st.button("Update")

    #######################
    # Dashboard Main Panel

    for key, d in st.session_state.shm_dict.items():

        d['container'] = st.expander(key, expanded=True)

        with d['container']:
            d['st_pyplot'] = st.empty()
            
            cols = st.columns(8, vertical_alignment="bottom")
            d['data_vmin'] = cols[0].number_input("vmin", min_value=None, max_value=None)
            d['data_vmax'] = cols[1].number_input("vmax", min_value=None, max_value=None)
            d['log_scale'] = cols[-2].toggle("Log Normalize")
            d['data_cbar'] = cols[-1].toggle("Color Bar", value=True)
    while True:
        try:
            for key, d in st.session_state.shm_dict.items():

                data = d['shm'].read_noblock()
                container = d['container']
                pyplot = d.get('st_pyplot')
                fig = d.get('fig')
                ax = d.get('ax')
                graph = d.get('graph')

                with container:
                    d_log_scale = 'logNorm' if d.get('log_scale') else None
                    plot, axes, graph = make_slope_plot(fig, ax, graph, data, d.get('data_vmin'), d.get('data_vmax'), d_log_scale)
                    
                    if d.get('data_cbar'):
                        divider = make_axes_locatable(axes[-1])
                        cax = divider.append_axes('right', size='5%', pad=0.05)
                        plot.colorbar(graph[-1], cax=cax, orientation='vertical')
                    
                    pyplot.pyplot(fig=plot, clear_figure=False) #, use_container_width=True)

                    d['fig'] = plot
                    d['ax'] = axes
                    d['graph'] = graph

        except Exception as e:
            print(f'error...{type(e)}')
            raise


if __name__ == '__main__':
    main()