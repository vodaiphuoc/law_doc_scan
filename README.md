#### Install env
1) create venv named `myenv`
```bash
python -m venv myenv
```
2) activate venv
```bash
myenv\Scripts\activate    // for Window
source myenv/bin/activate // for Linux
```

#### install dependencies
```bash
pip install -r scan_service/requirements.txt
```
#### run example
1) setup modal for remote compute (skip if already setup)
    - create account at [modal.com](https://modal.com/)
    - run setup
```bash
modal setup
```
2) deploy inference server
```bash
modal deploy inference_server/run_with_vllm.py
```
output from terminal may look like this:
```bash
 Created objects.
├── 🔨 Created mount 
│   ./inference_server/run_with_vllm.py
├── 🔨 Created mount ./commons
└── 🔨 Created web function serve => 
    https://<account>--inference-server-internvl3-serve.modal.run
✓ App deployed in 3.831s! 🎉
```
next,
**COPY** the url after 'Created web function serve =>'
open *commons/configs/model.py*, at line 21, **PASTE** the url

3) run scan_service
```bash
python scan_service/app.py --file_path QD-331-TW.pdf
```
where *QD-331-TW.pdf* is a example file
result will be available in terminal output
#### WARNING
- Fist time **run scan_service** may take time, due to vllm

#### Project structure
```
.
├── commons/                    # shared package
│   ├── configs
│   │   └── model.py
│   │   
│   ├── schemas/
│   │   ├── model.py
│   │   └── api.py
│   │   
│   └── logger.py
│
├── inference_server/           # for host LLM model
│   ├── Dockerfile
│   └── run_with_vllm.py
│
├── scan_service/               # service worker
│   ├── model/
│   │   ├── examples.py
│   │   └── infer.py
│   │
│   ├── utils.py
│   ├── app.py
│   ├── README.md
│   └── requirements.txt
│
├── main_app/                   # main service
|   ├── app.py
│   ├── README.md
│   └── requirements.txt
|
└── README.md
```

