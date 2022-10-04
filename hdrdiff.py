import argparse
import qt
import transform
from layout import HBox, VBox, Stretch
from functools import partial
from images import Images


def dims(obj):
    """Return (width, height) tuple for object with width() and height() methods."""
    return obj.width(), obj.height()


class ImageView(qt.QGraphicsView):
    def __init__(self, images, parent=None, **kwargs):
        scene = qt.QGraphicsScene()
        self._image_dims = dims(images.qimage)
        self._item = qt.QGraphicsPixmapItem(qt.QPixmap.fromImage(images.qimage))
        scene.addItem(self._item)

        super().__init__(scene=scene, parent=parent, **kwargs)
        self.setBackgroundBrush(qt.Qt.gray)
        self.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        images.imageChanged.connect(
            lambda i: self._item.setPixmap(qt.QPixmap.fromImage(i))
        )

        self._drag_state = None

    @property
    def _transform(self):
        return self._item.transform()

    @_transform.setter
    def _transform(self, t):
        self._item.setTransform(t)

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
            center=(evt.x(), evt.y()),
            increment=evt.angleDelta().y() / 240.0,
        )

    def mouseMoveEvent(self, evt):
        if evt.buttons() == qt.Qt.LeftButton:
            if self._drag_state is None:
                self._drag_state = (self._transform, (evt.x(), evt.y()))
                self.setCursor(qt.Qt.CursorShape.ClosedHandCursor)
            else:
                self._transform = transform.pan(*self._drag_state, (evt.x(), evt.y()))

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file1")
    parser.add_argument("file2", nargs="?")
    args = parser.parse_args()

    app = qt.QApplication([])
    window = qt.QWidget()
    images = Images(args.file1, args.file2)

    def set_number(slot, text):
        try:
            slot(float(text))
        except ValueError:
            pass

    view = ImageView(images, parent=window)
    info = qt.QLabel(parent=window)
    # Weird, keyword argument for connecting signals doesn't work here
    scale = qt.QLineEdit("1.0", window)
    scale.textChanged.connect(partial(set_number, images.set_scale))
    offset = qt.QLineEdit("0.0")
    offset.textChanged.connect(partial(set_number, images.set_offset))

    def do_normalize():
        s, o = images.normalize()
        scale.setText(f"{s:g}")
        offset.setText(f"{o:g}")

    normalize = qt.QPushButton("Normalize", clicked=do_normalize)

    diff_scale = qt.QLineEdit("1.0")
    diff_scale.textChanged.connect(partial(set_number, images.set_diff_scale))

    def do_normalize_diff():
        diff_scale.setText(f"{images.normalize_diff():g}")

    normalize_diff = qt.QPushButton("Normalize Diff", clicked=do_normalize_diff)

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
                            Stretch(2),
                            qt.QLabel("Diff Scale"),
                            diff_scale,
                            30,
                            normalize_diff,
                            Stretch(3),
                        ]
                    ),
                ]
            ),
            VBox(children=[info]),
        ],
    )

    # Shortcuts
    shortcuts = [
        Shortcut(window, *s)
        for s in [
            (
                "Zoom In",
                view.zoom_in,
                [qt.Qt.CTRL + qt.Qt.Key_Equal, qt.Qt.CTRL + qt.Qt.Key_Plus],
            ),
            ("Zoom Out", view.zoom_out, [qt.Qt.CTRL + qt.Qt.Key_Minus]),
            ("Reset Zoom", view.reset_view, [qt.Qt.CTRL + qt.Qt.Key_0]),
            (
                "Toggle Single-Channel View",
                images.view_channel,
                [qt.Qt.Key_R, qt.Qt.Key_G, qt.Qt.Key_B, qt.Qt.Key_A],
            ),
            ("View Left Image", lambda: images.select_image(0), [qt.Qt.Key_1]),
            ("View Right Image", lambda: images.select_image(1), [qt.Qt.Key_2]),
            ("View Diff", lambda: images.select_image(2), [qt.Qt.Key_3]),
            ("Normalize Diff", do_normalize_diff, [qt.Qt.Key_N]),
        ]
    ]
    info.setText("Shortcuts:\n" + "\n".join(s.description for s in shortcuts))

    # Run the app
    window.showMaximized()
    app.exec_()
