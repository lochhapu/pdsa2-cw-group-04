from PIL import Image, ImageTk
import math

class KnightSprite:
    def __init__(self, canvas, paths):
        self.canvas = canvas
        self.animations = {}
        self.pil_animations = {}
        self.current_state = "idle"
        self._mirrored_frames_cache = {}

        for state, path_info in paths.items():
            path = path_info['path']
            num_frames = path_info['frames']
            
            sheet = Image.open(path)
            frames = []
            pil_frames = []

            frame_width = sheet.width // num_frames
            for i in range(num_frames):
                frame = sheet.crop((i * frame_width, 0, (i + 1) * frame_width, sheet.height))
                pil_frames.append(frame)
                frames.append(ImageTk.PhotoImage(frame))
                
            self.animations[state] = frames
            self.pil_animations[state] = pil_frames
            self._mirrored_frames_cache[state] = None

        self.current_state = list(paths.keys())[0]
        self.image = canvas.create_image(0, 0, image=self.animations[self.current_state][0])

    def change_state(self, state):
        if state in self.animations:
            self.current_state = state
            self.canvas.itemconfig(self.image, image=self.animations[state][0])

    def move_to(self, x, y):
        self.canvas.coords(self.image, x, y)

    def animate_jump(self, start, end, callback=None):
        steps = 20
        delay = 30

        x1, y1 = start
        x2, y2 = end

        dx = (x2 - x1) / steps
        dy = (y2 - y1) / steps

        # Determine direction and get appropriate frames
        moving_left = x2 < x1
        self.change_state("jump")
        frames_to_use = self._get_mirrored_frames("jump") if moving_left else self.animations["jump"]

        step = 0

        def animate():
            nonlocal step

            if step <= steps:
                t = step / steps

                # arc jump
                height = 30
                arc = -4 * height * (t - 0.5) ** 2 + height

                x = x1 + dx * step
                y = y1 + dy * step - arc

                frame = step % len(frames_to_use)

                self.canvas.itemconfig(self.image, image=frames_to_use[frame])
                self.canvas.coords(self.image, x, y)

                step += 1
                self.canvas.after(delay, animate)
            else:
                self.change_state("idle")
                if callback:
                    callback()

        animate()

    def _get_mirrored_frames(self, state):
        """Return horizontally flipped frames for left movement"""
        if self._mirrored_frames_cache.get(state) is None:
            from PIL import ImageTk
            self._mirrored_frames_cache[state] = []
            for pil_image in self.pil_animations[state]:
                flipped = ImageTk.PhotoImage(pil_image.transpose(Image.FLIP_LEFT_RIGHT))
                self._mirrored_frames_cache[state].append(flipped)
        return self._mirrored_frames_cache[state]

    def animate_death(self, callback=None):
        self.change_state("death")
        frames_to_use = self.animations["death"]
        delay = 100
        step = 0

        def animate():
            nonlocal step
            if step < len(frames_to_use):
                self.canvas.itemconfig(self.image, image=frames_to_use[step])
                step += 1
                self.canvas.after(delay, animate)
            else:
                if callback:
                    callback()

        animate()