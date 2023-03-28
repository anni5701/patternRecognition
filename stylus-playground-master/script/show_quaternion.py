import numpy as np



import moderngl

import stl

import pyglet

import pyrr



import serial

from serial.tools.list_ports import comports



from ahrs.filters import Madgwick

from ahrs.common.orientation import acc2q





def normalize(v):

    norm = np.linalg.norm(v, axis=-1, keepdims=True)

    return v / norm



def create_from_vectors(a, b):

    # https://stackoverflow.com/a/11741520

    a = normalize(a)

    b = normalize(b)

    dot = np.dot(a, b)

    cross = -np.cross(a, b)

    q = normalize(np.stack([cross[..., 0], cross[..., 1], cross[..., 2], dot + 1], axis=-1))

    return q



def create_from_vector(v):

    ref = np.array([1.0, 0.0, 0.0])

    return create_from_vectors(ref, v)





class Reader:

    def __init__(self, port):

        self.port = port

        self.chunks = []



    def update(self):

        lines = []



        available = self.port.in_waiting

        if available > 0:

            chunk = port.read(available).decode("ascii")



            while "\n" in chunk:

                end = chunk.index("\n") + 1

                self.chunks.append(chunk[:end])

                

                line = "".join(self.chunks).rstrip()

                lines.append(line)



                self.chunks.clear()

                chunk = chunk[end:]

            

            self.chunks.append(chunk)



        return lines





port_name = None



# If none is provided, just take the first one

if port_name is None:

    info = comports()[0]

    port_name = info.device



# Connect to USB device

with serial.Serial(port_name, 9600, timeout=1) as port:

    reader = Reader(port)



    # Open window

    window = pyglet.window.Window(1020, 576, vsync=True)



    # Create OpenGL context

    ctx = moderngl.create_context()



    # Compile GLSL shader

    prog = ctx.program(

        vertex_shader="""

        #version 330 core



        layout(location = 0) in vec3 in_position;

        layout(location = 1) in vec3 in_normal;



        out vec3 v_position;

        out vec3 v_normal;



        uniform mat4 projection;

        uniform mat4 view;      

        uniform mat4 model;     



        void main() {

            gl_Position = projection * view * model * vec4(in_position, 1.0);

            v_position = (model * vec4(in_position, 1.0)).xyz;

            v_normal = (transpose(inverse(model)) * vec4(in_normal, 0.0)).xyz;

        }

        """,

        fragment_shader="""

        #version 330 core

        

        in vec3 v_position;

        in vec3 v_normal;



        out vec4 color;

        

        uniform vec3 model_color;

        uniform vec3 light_position;

        uniform vec3 light_direction;

        uniform float light_radius;



        void main() {

            float exposure = -dot(normalize(light_direction), normalize(v_normal));

            float distance = length(v_position - light_position);

            float ratio = max(exposure, 0.0) * max(light_radius - distance, 0.0);

            vec3 factor = vec3(0.8, 0.7, 0.9) * ratio + 0.1;

            color = vec4(factor * model_color, 1.0);

        }

        """,

    )



    # Load STL file

    mesh = stl.mesh.Mesh.from_file("../data/arrow.stl")

    vertices = mesh.points.reshape(-1, 3)

    normals = np.repeat(mesh.normals, 3, axis=0)



    # Create vertex buffer

    vbo_vertex = ctx.buffer(vertices)

    vbo_normal = ctx.buffer(normals)

    vao = ctx.vertex_array(prog, [

        (vbo_vertex, "3f", "in_position"),

        (vbo_normal, "3f", "in_normal"),

    ])



    # Create Madgwick filter

    madgwick = Madgwick()

    madgwick.t = None

    madgwick.a = np.array([0.0, 0.0, 1.0])

    madgwick.q = np.array([1.0, 0.0, 0.0, 0.0])



    @window.event

    def on_resize(width, height):

        # TODO

        return pyglet.event.EVENT_HANDLED



    @window.event

    def on_draw():



        # Clear color and depth buffers

        ctx.clear()

        ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)



        # Create perspective projection transform

        # Note: `pyrr` uses transposed matrices, i.e. use `m.T @ p` to transform a point!

        projection_matrix = pyrr.matrix44.create_perspective_projection(

            60,

            window.aspect_ratio,

            0.1,

            1000,

        )



        # Create camera transform

        view_matrix = pyrr.matrix44.create_look_at(

            [2.0, 2.0, 1.0],

            [0.0, 0.0, 0.0],

            [0.0, 0.0, 1.0],

        )



        # Get estimated quaternion, in `pyrr` format

        # Note: this is the transformation from navigation frame to sensor frame

        q_ns = madgwick.q[[1, 2, 3, 0]]



        # Get transformation from sensor frame to navigation frame

        q_sn = pyrr.quaternion.conjugate(q_ns)



        # Get associated rotation matrix, with homogeneous coordinate

        R_sn = pyrr.matrix44.create_from_quaternion(q_sn)



        # Get measured acceleration in navigation frame

        a_s = madgwick.a

        a_n = R_sn[:3, :3].T @ a_s



        # Get transformation matrix for acceleration arrow

        # Note: matrices must be composed from left to right (i.e. left-most is applied first)

        q_a = create_from_vector(a_n)

        s_a = np.linalg.norm(a_n)

        R_a = pyrr.matrix44.create_from_scale([s_a, 1.0, 1.0]) @ pyrr.matrix44.create_from_quaternion(q_a)



        # Get transform from [1, 0, 0] to [0, 1, 0] and [0, 0, 1], respectively

        R_ex = pyrr.matrix44.create_identity()

        R_ey = pyrr.matrix44.create_from_z_rotation(-np.pi / 2)

        R_ez = pyrr.matrix44.create_from_y_rotation(np.pi / 2)



        # Sensor frame arrows

        x_arrow = (1.0, 0.2, 0.2), R_ex @ R_sn

        y_arrow = (0.2, 1.0, 0.2), R_ey @ R_sn

        z_arrow = (0.2, 0.2, 1.0), R_ez @ R_sn



        # Navigation frame arrows

        ex_arrow = (0.5, 0.2, 0.2), R_ex

        ey_arrow = (0.2, 0.5, 0.2), R_ey

        ez_arrow = (0.2, 0.2, 0.5), R_ez



        # Acceleration arrow

        # Note: this should roughly points up, as this is dominated by gravity

        a_arrow = (1.0, 1.0, 0.2), R_a



        # Pack all arrows as single list, for convenience

        arrows = [

            ex_arrow,

            ey_arrow,

            ez_arrow,

            x_arrow,

            y_arrow,

            z_arrow,

            a_arrow,

        ]



        # Set uniforms

        # Note: `pyrr` transposed format is convenient, as uniform matrices are expected row-wise

        prog["projection"] = projection_matrix.flatten()

        prog["view"] = view_matrix.flatten()

        prog["light_position"] = [0.0, -5.0, 2.0]

        prog["light_direction"] = [-0.5, -0.5, -1.0]

        prog["light_radius"] = 8.0



        # Draw triangles

        for color, model_matrix in arrows:

            prog["model"] = model_matrix.flatten()

            prog["model_color"] = color

            vao.render()



    # This gets executed at each "frame"

    def tick(dt):



        # Handle pending input from Arduino

        lines = reader.update()

        for line in lines:

            args = line.strip().split(",")

            if len(args) == 8:



                # A few comments on reference frames:

                #  - `ahrs` uses X-right, Y-forward, Z-up as body frame

                #  - We use X-forward (pen tip), Y-left, Z-up (upward w.r.t. sensor PCB, at least)

                #  - Navigation frame is X-East, Y-North, Z-up (a.k.a. ENU)

                #  - In our case, magnetic field is not measured, so there is not any known anchor horizontally



                # Parse line, convert to expected units

                t = int(args[0]) * 1e-3

                a = np.array([float(args[1]), float(args[2]), float(args[3])])

                g = np.array([float(args[4]), float(args[5]), float(args[6])]) * (np.pi / 180.0)



                # If this is the first iteration, roughly estimate orientation using gravity only

                if madgwick.t is None:

                    madgwick.q = acc2q(a)



                # Otherwise, apply Madgwick filter to update orientation estimation

                else:

                    madgwick.Dt = t - madgwick.t

                    madgwick.q = madgwick.updateIMU(madgwick.q, g, a)



                # Also keep latest timestamp and measured acceleration

                madgwick.t = t

                madgwick.a = a



    # Schedule relatively fast update

    pyglet.clock.schedule_interval(tick, 0.02)



    pyglet.app.run()
