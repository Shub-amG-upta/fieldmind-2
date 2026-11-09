/* FieldMind agent on the QIDK (reports/sched_stage_b.md). The official CPython
   Android release is embeddable only (libpython, no executable); this is the
   whole interpreter front end: `fieldmind-python run_demo.py ...` behaves like
   `python3 run_demo.py ...`. Built by `bench.device_agent launcher`. */
extern int Py_BytesMain(int argc, char **argv);

int main(int argc, char **argv) { return Py_BytesMain(argc, argv); }
