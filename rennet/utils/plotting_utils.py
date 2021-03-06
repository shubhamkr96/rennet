#  Copyright 2018 Fraunhofer IAIS. All rights reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
"""Utilities for plotting

@motjuste
Created: 08-10-2016
"""
from __future__ import division, print_function, absolute_import
from math import ceil
import matplotlib.pyplot as plt
import numpy as np
from six.moves import range
from librosa.display import specshow

from .np_utils import normalize_confusion_matrix


def plot_multi(  # pylint: disable=too-many-arguments, too-many-locals, too-many-branches, too-complex
        x_list,
        *args,
        func="plot",
        rows=None,
        cols=4,
        perfigsize=(4, 4),
        subplot_titles=None,
        labels=None,
        fig_title=None,
        show=True,
        **kwargs):
    if rows is None:
        rows = ceil(len(x_list) / cols)

    fgsz = (perfigsize[0] * cols, perfigsize[1] * rows)
    fig, axs = plt.subplots(rows, cols, figsize=fgsz)

    if len(x_list) == 1:
        axs = [axs]

    fig.suptitle(fig_title)

    at = lambda i: divmod(i, cols)
    if rows == 1:
        at = lambda i: i

    if labels is None:
        labels = [None for _ in range(len(x_list))]

    if subplot_titles is None:
        subplot_titles = list(range(len(x_list)))

    if func == "plot":
        for i, x_i in enumerate(x_list):
            axs[at(i)].plot(x_i, label=labels[i], *args, **kwargs)
    elif func == "pie":
        for i, x_i in enumerate(x_list):
            axs[at(i)].pie(x_i, labels=labels[i], *args, **kwargs)
            axs[at(i)].axis("equal")
    elif func == "hist":
        for i, x_i in enumerate(x_list):
            axs[at(i)].hist(x_i, *args, **kwargs)
    elif func == "imshow":
        for i, x_i in enumerate(x_list):
            axs[at(i)].imshow(x_i, *args, **kwargs)
    elif func == "confusion":
        # Find confusion specific kwargs, and pop them before forwarding

        # REF: http://stackoverflow.com/questions/11277432
        fontcolor = kwargs.pop('conf_fontcolor', None)
        fontcolor = 'red' if fontcolor is None else fontcolor

        fontsize = kwargs.pop('conf_fontsize', None)
        fontsize = 16 if fontsize is None else fontsize
        for i, x_i in enumerate(x_list):
            # plotting the colors
            axs[at(i)].imshow(x_i, interpolation='none', *args, **kwargs)
            axs[at(i)].set_aspect(1)

            # REF: http://stackoverflow.com/questions/20416609
            axs[at(i)].set_xticklabels([])
            axs[at(i)].set_yticklabels([])

            axs[at(i)].set_xticks([0.5 + 1 * _i for _i in range(len(x_i))])
            axs[at(i)].set_yticks([0.5 + 1 * _i for _i in range(len(x_i))])
            axs[at(i)].grid(True, linestyle=':')

            # adding text for values
            for x in range(x_i.shape[0]):  # width
                for y in range(x_i.shape[1]):  # height
                    axs[at(i)].annotate(
                        "{:.2f}%".format(x_i[x][y] * 100),
                        xy=(y, x),
                        horizontalalignment='center',
                        verticalalignment='center',
                        color=fontcolor,
                        fontsize=fontsize
                    )
    else:
        raise ValueError("Unsupported plotting function {}".format(func))

    for i, subplot_title in enumerate(subplot_titles):
        axs[at(i)].set_title(subplot_title)

    if show:
        plt.show()


def plot_speclike(  # pylint: disable=too-many-arguments
        orderedlist,
        figsize=(20, 4),
        show_time=False,
        sr=16000,
        hop_sec=0.05,
        cmap='viridis',
        show=True):
    assert all(o.shape[0] == orderedlist[0].shape[0]
               for o in orderedlist), "All list items should be of the same length"

    x_axsis = 'time' if show_time else None
    hop_len = int(hop_sec * sr)

    plt.figure(figsize=figsize)
    specshow(
        np.vstack(reversed(orderedlist)),
        x_axis=x_axsis,
        sr=sr,
        hop_length=hop_len,
        cmap=cmap,
    )
    plt.colorbar()

    if show:
        plt.show()


def _plot_normalized_confusion_mat(  # pylint: disable=too-many-arguments
        confusion_matrix,
        *args,
        figsize=(4, 4),
        cmap='Blues',
        fontcolor='red',
        fontsize=16,
        figtitle='Confusion Matrix',
        subplot_title="",
        show=True,
        **kwargs):
    plot_multi(
        [confusion_matrix],
        func="confusion",
        rows=1,
        cols=1,
        perfigsize=figsize,
        fig_title=figtitle,
        subplot_titles=[subplot_title],
        show=show,
        # add these at end as part of kwargs
        conf_fontsize=fontsize,
        conf_fontcolor=fontcolor,
        cmap=cmap,
        *args,
        **kwargs
    )


plot_normalized_confusion_matrix = _plot_normalized_confusion_mat  # pylint: disable=invalid-name

def plot_confusion_precision_recall(  # pylint: disable=too-many-arguments
        conf_precision,
        conf_recall,
        *args,
        perfigsize=(4, 4),
        cmap='Blues',
        fontcolor='red',
        fontsize=16,
        figtitle='Confusion Matrix',
        subplot_titles=('Precision', 'Recall'),
        show=True,
        **kwargs):
    plot_multi(
        [conf_precision, conf_recall],
        func="confusion",
        rows=1,
        cols=2,
        perfigsize=perfigsize,
        fig_title=figtitle,
        subplot_titles=subplot_titles,
        show=show,
        # add these at end as part of kwargs
        conf_fontsize=fontsize,
        conf_fontcolor=fontcolor,
        cmap=cmap,
        *args,
        **kwargs
    )


def plot_confusion_history(  # pylint: disable=too-many-arguments, too-many-locals
        confusion_matrices,
        figsize=(20, 8),
        fig_title="Confusions History",
        marker='|',
        colors_for_true=('grey', 'yellowgreen', 'lightcoral'),
        linestyles_for_tp=('-'),
        linestyles_for_fp=(':', '--', '-.'),
):
    prec_rec = normalize_confusion_matrix(confusion_matrices)

    fig, axs = plt.subplots(2, 1, figsize=figsize)

    fig.suptitle(fig_title)
    axstitles = ('Precision', 'Recall')

    cyclic = lambda l, i: l[i % len(l)]

    color = lambda t: cyclic(colors_for_true, t)

    linestyles = [linestyles_for_fp, linestyles_for_tp]
    line = lambda t, p: cyclic(linestyles[t == p], [p, t][t == p])

    true_nc, pred_nc = prec_rec[0].shape[-2:]
    for i, con in enumerate(prec_rec):
        for t in range(true_nc):
            for p in range(pred_nc):
                axs[i].plot(
                    con[:, t, p],
                    color=color(t),
                    linestyle=line(t, p),
                    label="{}_{}".format(t, p),
                    marker=marker,
                )
                axs[i].set_ylim([0, 1])

        axs[i].legend()
        axs[i].set_title(axstitles[i])
        axs[i].grid()
