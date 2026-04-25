// Minimal OpenGL ES 3.1 fragment-shader stressor (headless, pbuffer surface).
// Compiles with Android NDK. Runs a heavy fragment loop continuously and
// prints frames-per-second once per second.
#include <EGL/egl.h>
#include <GLES3/gl31.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static const char *VS =
    "#version 310 es\n"
    "const vec2 V[3] = vec2[](vec2(-1.0,-1.0), vec2(3.0,-1.0), vec2(-1.0,3.0));\n"
    "void main(){ gl_Position = vec4(V[gl_VertexID], 0.0, 1.0); }\n";

// Fragment shader: lots of trigs + sqrt per pixel to saturate ALU
static const char *FS =
    "#version 310 es\n"
    "precision highp float;\n"
    "out vec4 fragColor;\n"
    "uniform float uTime;\n"
    "void main(){\n"
    "  vec2 p = gl_FragCoord.xy * 0.001 + uTime;\n"
    "  float a = 0.0;\n"
    "  for (int i = 0; i < 128; i++) {\n"
    "    p = vec2(sin(p.y*1.3)+uTime, cos(p.x*1.7)-uTime);\n"
    "    a += sqrt(dot(p,p)) * 0.0001;\n"
    "    p *= 1.02;\n"
    "  }\n"
    "  fragColor = vec4(a, fract(a*2.0), fract(a*3.0), 1.0);\n"
    "}\n";

static GLuint build(GLenum t, const char* s) {
    GLuint sh = glCreateShader(t);
    glShaderSource(sh, 1, &s, NULL);
    glCompileShader(sh);
    GLint ok; glGetShaderiv(sh, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        char log[2048]; GLsizei n = 0;
        glGetShaderInfoLog(sh, sizeof(log), &n, log);
        fprintf(stderr, "shader err: %.*s\n", n, log);
        exit(1);
    }
    return sh;
}

int main(int argc, char** argv) {
    int W = argc > 1 ? atoi(argv[1]) : 1280;
    int H = argc > 2 ? atoi(argv[2]) : 720;

    EGLDisplay dpy = eglGetDisplay(EGL_DEFAULT_DISPLAY);
    if (dpy == EGL_NO_DISPLAY) { fprintf(stderr, "no EGL display\n"); return 1; }
    if (!eglInitialize(dpy, NULL, NULL)) { fprintf(stderr, "eglInit fail\n"); return 1; }

    const EGLint cfg_attr[] = {
        EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES3_BIT,
        EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8,
        EGL_NONE };
    EGLConfig cfg; EGLint ncfg;
    if (!eglChooseConfig(dpy, cfg_attr, &cfg, 1, &ncfg) || ncfg < 1) {
        fprintf(stderr, "eglChooseConfig fail\n"); return 1;
    }

    const EGLint surf_attr[] = { EGL_WIDTH, W, EGL_HEIGHT, H, EGL_NONE };
    EGLSurface surf = eglCreatePbufferSurface(dpy, cfg, surf_attr);
    if (surf == EGL_NO_SURFACE) { fprintf(stderr, "pbuffer surf fail 0x%x\n", eglGetError()); return 1; }

    const EGLint ctx_attr[] = { EGL_CONTEXT_CLIENT_VERSION, 3, EGL_NONE };
    EGLContext ctx = eglCreateContext(dpy, cfg, EGL_NO_CONTEXT, ctx_attr);
    if (ctx == EGL_NO_CONTEXT) { fprintf(stderr, "ctx fail\n"); return 1; }
    if (!eglMakeCurrent(dpy, surf, surf, ctx)) { fprintf(stderr, "make current fail\n"); return 1; }

    printf("GLES vendor=%s renderer=%s version=%s viewport=%dx%d\n",
           glGetString(GL_VENDOR), glGetString(GL_RENDERER),
           glGetString(GL_VERSION), W, H);
    fflush(stdout);

    GLuint vs = build(GL_VERTEX_SHADER, VS);
    GLuint fs = build(GL_FRAGMENT_SHADER, FS);
    GLuint prog = glCreateProgram();
    glAttachShader(prog, vs); glAttachShader(prog, fs);
    glLinkProgram(prog);
    glUseProgram(prog);
    GLint u_time = glGetUniformLocation(prog, "uTime");
    glViewport(0, 0, W, H);

    GLuint vao; glGenVertexArrays(1, &vao); glBindVertexArray(vao);

    struct timespec t0, ts;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    long frames = 0, total_frames = 0;
    long next_report = 1;

    while (1) {
        glUniform1f(u_time, (float)total_frames * 0.016f);
        glDrawArrays(GL_TRIANGLES, 0, 3);
        glFinish();
        eglSwapBuffers(dpy, surf);
        frames++;
        total_frames++;

        clock_gettime(CLOCK_MONOTONIC, &ts);
        double elapsed = (ts.tv_sec - t0.tv_sec) + (ts.tv_nsec - t0.tv_nsec) / 1e9;
        if (elapsed >= next_report) {
            printf("t=%.1fs fps=%.1f total=%ld\n", elapsed, frames / (elapsed - (next_report - 1)), total_frames);
            fflush(stdout);
            frames = 0;
            next_report += 1;
            // Reset per-second window
            t0 = ts;
            next_report = 1;
        }
    }
    return 0;
}
