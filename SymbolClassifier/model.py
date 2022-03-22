from pickletools import optimize
from matplotlib.pyplot import axis
from tf.keras.layers import Input, Conv2D, Flatten, Dense, Concatenate
from tf.keras.layers import MaxPooling2D, UpSampling2D, Dropout
from tf.keras.models import Model

class SymbolCNN:

    def get_conv_block(self, input_img, filters, kernel, pooling_kernel):
        x = input_img
        for idx, f in enumerate(filters):
            x = Conv2D(f, kernel, activation='relu', padding='same')(x)
            x = MaxPooling2D(pooling_kernel, stride=(2,2))(x)
            x = Dropout(0.25)(x)
        
        return x

    def model(self, img_heigth, img_width, epochs, generator, steps, cats_glyph, cats_pos):
        #
        # if its glyph --> 40 x 40
        #
        # if its position --> 40 x 112

        filters = [32, 32, 64, 64]
        kernel = (3,3)
        pooling_kernel = (2,2)

        input_img_glyph = Input(shape=(img_heigth, img_width, 1))
        input_img_pos   = Input(shape=(img_heigth, img_width, 1))
        
        x_glyph = self.get_conv_block(input_img_glyph, filters, kernel, pooling_kernel)
        x_pos   = self.get_conv_block(input_img_pos, filters, kernel, pooling_kernel)

        x_glyph = Flatten()(x_glyph) # (bs, h/8, w/8, 64) -> (bs, f) -- f = h/8*w/8*64
        x_pos   = Flatten()(x_pos)   # (bs, h/8, w/8, 64) -> (bs, f) -- f = h/8*w/8*64

        x_concat = Concatenate(axis=1)([x_glyph,x_pos])

        x_ff = Dense(256)(x_concat)
        x_ff = Dropout(0.25)

        out_glyph  = Dense(cats_glyph, activation="softmax")(x_ff)
        out_pos    = Dense(cats_pos, activation="softmax")(x_ff)

        # Crear un generador que devuelva los dos batches de datos
        model = Model(inputs=[input_img_glyph, input_img_pos], output=[out_glyph, out_pos])

        model.compile(optimizer='RMSprop')