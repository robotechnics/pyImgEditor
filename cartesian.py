"""
Copyright (C) 2017  Bernard Virot

bLUe - Photo editing software.

With Blue you can enhance and correct the colors of your photos in a few clicks.
No need for complex tools such as lasso, magic wand or masks.
bLUe interactively constructs 3D LUTs (Look Up Tables), adjusting the exact set
of colors you want.

3D LUTs are widely used by professional film makers, but the lack of
interactive tools maked them poorly useful for photo enhancement, as the shooting conditions
can vary widely from an image to another. With bLUe, in a few clicks, you select the set of
colors to modify, the corresponding 3D LUT is automatically built and applied to the image.
You can then fine tune it as you want.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""

# the code below is taken from the site https://gist.github.com/hernamesbarbara/68d073f551565de02ac5
# We gratefully acknowledge the contribution of the author.

import numpy as np

def cartesianProduct(arrayList, out=None):
    """
    Build the cartesian product of
    several 1-D array-like objects as a numpy array

    :param arrayList : list or tuple of 1-D array-like objects
    :param out : only used by recursive calls
    :return 2-D array of shape (M, len(arrays))

    """
    arrayList = [np.asarray(x) for x in arrayList]
    n = np.prod([x.size for x in arrayList])

    # empty product
    if n == 0:
        return np.array([])

    # size of item in product
    itemSize = len(arrayList)

    dtype = arrayList[0].dtype

    for a in arrayList[1:]:
        if a.dtype != dtype:
            raise ValueError("cartesianProduct : all arrays must have the same dtype")

    m = n / arrayList[0].size
    if out is None:
        out = np.zeros([n, itemSize], dtype=dtype)
    out[:,0] = np.repeat(arrayList[0], m)

    if arrayList[1:]:
        cartesianProduct(arrayList[1:], out=out[0:m, 1:])
        for j in xrange(1, arrayList[0].size):
            out[j*m:(j+1)*m,1:] = out[0:m,1:]
    dims = tuple([x.size for x in arrayList]+[len(arrayList)])
    return np.reshape(out, dims)