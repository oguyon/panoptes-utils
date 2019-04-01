from copy import copy

from matplotlib import rc
from matplotlib import animation
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import cm
import numpy as np

from astropy.visualization import LogStretch, ImageNormalize, LinearStretch, MinMaxInterval
from photutils import RectangularAperture

rc('animation', html='html5')


def get_palette(cmap='inferno'):
    """Get a palette for drawing.

    Returns a copy of the colormap palette with bad pixels marked.

    Args:
        cmap (str, optional): Colormap to use, default 'inferno'.

    Returns:
        `matplotlib.cm`: The colormap.
    """
    palette = copy(getattr(cm, cmap))
    palette.set_over('w', 1.0)
    palette.set_under('k', 1.0)
    palette.set_bad('g', 1.0)
    return palette


def add_pixel_grid(ax1, grid_height, grid_width, show_axis_labels=True, show_superpixel=False,
                   major_alpha=0.5, minor_alpha=0.25):

    # major ticks every 2, minor ticks every 1
    if show_superpixel:
        x_major_ticks = np.arange(-0.5, grid_width, 2)
        y_major_ticks = np.arange(-0.5, grid_height, 2)

        ax1.set_xticks(x_major_ticks)
        ax1.set_yticks(y_major_ticks)

        ax1.grid(which='major', color='r', linestyle='--', lw=3, alpha=major_alpha)
    else:
        ax1.set_xticks([])
        ax1.set_yticks([])

    x_minor_ticks = np.arange(-0.5, grid_width, 1)
    y_minor_ticks = np.arange(-0.5, grid_height, 1)

    ax1.set_xticks(x_minor_ticks, minor=True)
    ax1.set_yticks(y_minor_ticks, minor=True)

    ax1.grid(which='minor', color='r', lw='2', linestyle='--', alpha=minor_alpha)

    if show_axis_labels is False:
        ax1.set_xticklabels([])
        ax1.set_yticklabels([])


def animate_stamp(d0):

    fig = Figure()
    FigureCanvas(fig)

    ax = fig.add_subplot(111)
    ax.set_xticks([])
    ax.set_yticks([])

    line = ax.imshow(d0[0])
    ax.set_title(f'Frame 0')

    def animate(i):
        line.set_data(d0[i])  # update the data
        ax.set_title(f'Frame {i:03d}')
        return line,

    # Init only required for blitting to give a clean slate.
    def init():
        line.set_data(d0[0])
        return line,

    ani = animation.FuncAnimation(fig, animate, np.arange(0, len(d0)), init_func=init,
                                  interval=500, blit=True)

    return ani


def show_stamps(pscs,
                frame_idx=None,
                stamp_size=11,
                aperture_position=None,
                aperture_size=None,
                show_residual=False,
                stretch=None,
                save_name=None,
                show_max=False,
                show_pixel_grid=False,
                **kwargs):

    if aperture_position is None:
        midpoint = (stamp_size - 1) / 2
        aperture_position = (midpoint, midpoint)

    if aperture_size:
        aperture = RectangularAperture(
            aperture_position, w=aperture_size, h=aperture_size, theta=0)

    ncols = len(pscs)

    if show_residual:
        ncols += 1

    nrows = 1

    fig = Figure()
    FigureCanvas(fig)
    fig.set_figheight(4)
    fig.set_figwidth(8)

    if frame_idx is not None:
        s0 = pscs[0][frame_idx]
        s1 = pscs[1][frame_idx]
    else:
        s0 = pscs[0]
        s1 = pscs[1]

    if stretch == 'log':
        stretch = LogStretch()
    else:
        stretch = LinearStretch()

    norm = ImageNormalize(s0, interval=MinMaxInterval(), stretch=stretch)

    ax1 = fig.add_subplot(nrows, ncols, 1)

    im = ax1.imshow(s0, cmap=get_palette(), norm=norm)

    if aperture_size:
        aperture.plot(color='r', lw=4, ax=ax1)
        # annulus.plot(color='c', lw=2, ls='--', ax=ax1)

    # create an axes on the right side of ax. The width of cax will be 5%
    # of ax and the padding between cax and ax will be fixed at 0.05 inch.
    # https://stackoverflow.com/questions/18195758/set-matplotlib-colorbar-size-to-match-graph
    divider = make_axes_locatable(ax1)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    fig.colorbar(im, cax=cax)
    ax1.set_title('Target')

    # Comparison
    ax2 = fig.add_subplot(nrows, ncols, 2)
    im = ax2.imshow(s1, cmap=get_palette(), norm=norm)

    if aperture_size:
        aperture.plot(color='r', lw=4, ax=ax1)
        # annulus.plot(color='c', lw=2, ls='--', ax=ax1)

    divider = make_axes_locatable(ax2)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    fig.colorbar(im, cax=cax)
    ax2.set_title('Comparison')

    if show_pixel_grid:
        add_pixel_grid(ax1, stamp_size, stamp_size, show_superpixel=False)
        add_pixel_grid(ax2, stamp_size, stamp_size, show_superpixel=False)

    if show_residual:
        ax3 = fig.add_subplot(nrows, ncols, 3)

        # Residual
        residual = s0 - s1
        im = ax3.imshow(residual, cmap=get_palette(), norm=ImageNormalize(
            residual, interval=MinMaxInterval(), stretch=LinearStretch()))

        divider = make_axes_locatable(ax3)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        fig.colorbar(im, cax=cax)
        ax3.set_title('Noise Residual')
        ax3.set_title('Residual RMS: {:.01%}'.format(residual.std()))
        ax3.set_yticklabels([])
        ax3.set_xticklabels([])

        if show_pixel_grid:
            add_pixel_grid(ax1, stamp_size, stamp_size, show_superpixel=False)

    # Turn off tick labels
    ax1.set_yticklabels([])
    ax1.set_xticklabels([])
    ax2.set_yticklabels([])
    ax2.set_xticklabels([])

    if save_name:
        try:
            fig.savefig(save_name)
        except Exception as e:
            warn("Can't save figure: {}".format(e))

    return fig