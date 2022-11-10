class Config:
    WIDTH = 640
    HEIGHT = 480
    FPS = 50

    @classmethod
    def to_dict(cls):
        return {
            k: v for k, v in cls.__dict__.items()
            if not k.startswith("__") and not callable(getattr(cls, k))
        }


if __name__ == '__main__':
    c = Config()
    print(c.to_dict())
