import argparse
import sys
import qt
import transform
from layout import HBox, VBox, Stretch
from functools import partial
from images import Images
from numberwidget import NumberWidget


def dims(obj):
    """Return (width, height) tuple for object with width() and height() methods."""
    return obj.width(), obj.height()


def position(evt):
    """Position of an event (e.g. QMouseEvent).

    Compatibility shim for PyQt 5/6."""
    try:
        # Qt 5
        return evt.localPos()
    except AttributeError:
        # Qt 6
        return evt.position()


class ImageView(qt.QGraphicsView):
    imageMouseOver = qt.Signal(qt.QPoint)

    def __init__(self, images, parent=None, **kwargs):
        scene = qt.QGraphicsScene()
        self._image_dims = dims(images.qimage)
        self._item = qt.QGraphicsPixmapItem(qt.QPixmap.fromImage(images.qimage))
        scene.addItem(self._item)

        super().__init__(parent=parent, **kwargs)
        self.setScene(scene)
        self.setBackgroundBrush(qt.Qt.gray)
        self.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        images.imageChanged.connect(
            lambda i: self._item.setPixmap(qt.QPixmap.fromImage(i))
        )
        self._last_mouse_position = None

        def update_mouseover():
            if self._last_mouse_position:
                self._emit_mouse_over(self._last_mouse_position)

        images.imageChanged.connect(update_mouseover)

        self._drag_state = None

    @property
    def _transform(self):
        return self._item.transform()

    @_transform.setter
    def _transform(self, t):
        self._item.setTransform(t)

    def _emit_mouse_over(self, point):
        self.imageMouseOver.emit(self._item.mapFromScene(point).toPoint())

    def resizeEvent(self, evt):
        super().resizeEvent(evt)

        if evt.spontaneous():
            return

        self.setSceneRect(0, 0, self.width(), self.height())
        self.reset_view()

    def wheelEvent(self, evt):
        # Delta of one wheel click is usually 120
        self._transform = transform.zoom(
            self._transform,
            center=(position(evt).x(), position(evt).y()),
            increment=evt.angleDelta().y() / 240.0,
        )

    def mouseMoveEvent(self, evt):
        self._last_mouse_position = position(evt)
        if evt.buttons() == qt.Qt.LeftButton:
            if self._drag_state is None:
                self._drag_state = (
                    self._transform,
                    (position(evt).x(), position(evt).y()),
                )
                self.setCursor(qt.Qt.CursorShape.ClosedHandCursor)
            else:
                self._transform = transform.pan(
                    *self._drag_state, (position(evt).x(), position(evt).y())
                )
        else:
            self.imageMouseOver.emit(self._item.mapFromScene(position(evt)).toPoint())

    def mouseReleaseEvent(self, evt):
        self._drag_state = None
        self.setCursor(qt.Qt.CursorShape.ArrowCursor)

    def reset_view(self):
        self._transform = transform.fit(self._image_dims, dims(self.sceneRect()))

    def zoom_in(self):
        self._transform = transform.zoom(
            self._transform,
            tuple(0.5 * i for i in dims(self.sceneRect())),
            increment=0.5,
        )

    def zoom_out(self):
        self._transform = transform.zoom(
            self._transform,
            tuple(0.5 * i for i in dims(self.sceneRect())),
            increment=-0.5,
        )


class Shortcut(qt.QObject):
    activated = qt.Signal(str)

    def __init__(self, widget, description, slot, keys):
        super().__init__()

        self.activated.connect(slot)
        sequences = [qt.QKeySequence(k) for k in keys]

        self._shortcuts = [
            qt.QShortcut(
                s, widget, activated=partial(self.activated.emit, s.toString())
            )
            for s in sequences
        ]
        self.description = (
            ", ".join(s.toString() for s in sequences) + f": {description}"
        )


def info_text(point, images):
    x, y = point.x(), point.y()

    def image_string(i):
        selected = i == images.selected_image
        try:
            width, height = images.image_dims[i]
            description = f"{width} x {height}, {images.descriptions[i]}"
        except IndexError:
            # No dims for diff
            description = f"{images.descriptions[i]}"
        try:
            pixel = images.cv_images[i][y][x]
        except IndexError:
            pixel = (0, 0, 0, 0)
        return f"""{"<b>" if selected else ""}{images.image_names[i]}
&nbsp;&nbsp;{description}
R: {pixel[2]:g}
G: {pixel[1]:g}
B: {pixel[0]:g}
A: {pixel[3]:g}
{"</b>" if selected else ""}
"""

    return (
        f"{x}, {y}\n\n"
        + "\n\n".join(image_string(i) for i in range(len(images.cv_images)))
    ).replace("\n", "<br>")


def console_diff(images):
    if not images.has_diff or images.max_diff == 0:
        return 0

    print(f"Maximum diff: {images.max_diff}")
    return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file1")
    parser.add_argument("file2", nargs="?")
    parser.add_argument(
        "-n", "--no-gui", help="Print diff information and exit.", action="store_true"
    )
    parser.add_argument(
        "-x",
        "--exit-if-same",
        help="Only show GUI if images differ.",
        action="store_true",
    )
    args = parser.parse_args()

    images = Images(args.file1, args.file2)
    if args.no_gui:
        sys.exit(console_diff(images))
    if args.exit_if_same and images.has_diff and images.max_diff == 0:
        sys.exit(0)

    app = qt.QApplication([])
    window = qt.QWidget()

    image_info = qt.QLabel(parent=window)
    image_info.setTextFormat(qt.Qt.RichText)
    # Prevent layout from wobbling as label contents change. Fixed
    # width is not ideal, but good enough for now.
    image_info.setFixedWidth(200)
    image_info.setWordWrap(True)
    shortcut_info = qt.QLabel(parent=window)
    view = ImageView(images, parent=window)
    view.imageMouseOver.connect(lambda p: image_info.setText(info_text(p, images)))
    scale = NumberWidget(1.0, min_value=0, parent=window)
    scale.valueChanged.connect(images.set_scale)
    offset = NumberWidget(0.0)
    offset.valueChanged.connect(images.set_offset)

    def do_normalize():
        s, o = images.normalize()
        scale.set_value(s)
        offset.set_value(o)

    def do_reset():
        scale.set_value(1.0)
        offset.set_value(0.0)

    normalize = qt.QPushButton("Normalize", clicked=do_normalize)
    reset = qt.QPushButton("Reset", clicked=do_reset)

    diff_scale = NumberWidget(1.0, min_value=0, parent=window)
    diff_scale.valueChanged.connect(images.set_diff_scale)

    def do_normalize_diff():
        diff_scale.set_value(images.normalize_diff())

    def do_reset_diff():
        diff_scale.set_value(1.0)

    normalize_diff = qt.QPushButton("Normalize Diff", clicked=do_normalize_diff)
    reset_diff = qt.QPushButton("Reset Diff", clicked=do_reset_diff)

    HBox(
        window,
        margin=8,
        children=[
            VBox(
                children=[
                    view,
                    HBox(
                        children=[
                            qt.QLabel("Scale"),
                            scale,
                            qt.QLabel("Offset"),
                            offset,
                            30,
                            normalize,
                            reset,
                            Stretch(2),
                            qt.QLabel("Diff Scale"),
                            diff_scale,
                            30,
                            normalize_diff,
                            reset_diff,
                            Stretch(3),
                        ]
                    ),
                ]
            ),
            VBox(children=[image_info, shortcut_info]),
        ],
    )

    def toggle_normalize():
        if images.selected_image == 2:
            if diff_scale.value == 1.0:
                do_normalize_diff()
            else:
                do_reset_diff()
        else:
            if scale.value == 1.0 and offset.value == 0.0:
                do_normalize()
            else:
                do_reset()

    # Shortcuts
    shortcuts = [
        Shortcut(window, *s)
        for s in [
            (
                "Zoom In",
                view.zoom_in,
                [qt.Qt.CTRL | qt.Qt.Key_Equal, qt.Qt.CTRL | qt.Qt.Key_Plus],
            ),
            ("Zoom Out", view.zoom_out, [qt.Qt.CTRL | qt.Qt.Key_Minus]),
            ("Reset Zoom", view.reset_view, [qt.Qt.CTRL | qt.Qt.Key_0]),
            (
                "Toggle Single-Channel View",
                images.view_channel,
                [qt.Qt.Key_R, qt.Qt.Key_G, qt.Qt.Key_B, qt.Qt.Key_A],
            ),
            ("View Left Image", lambda: images.select_image(0), [qt.Qt.Key_1]),
            ("View Right Image", lambda: images.select_image(1), [qt.Qt.Key_2]),
            ("View Diff", lambda: images.select_image(2), [qt.Qt.Key_3]),
            ("Normalize/Reset", toggle_normalize, [qt.Qt.Key_N]),
            ("Quit", window.close, [qt.Qt.Key_Q, qt.Qt.Key_Escape]),
        ]
    ]
    shortcut_info.setText("Shortcuts:\n" + "\n".join(s.description for s in shortcuts))

    # Run the app
    window.showMaximized()
    app.exec_()
