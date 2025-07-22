#### Install env
- create venv named `myenv`
```bash
python -m venv myenv
```
- activate venv
    - for Window
```bash
myenv\Scripts\activate
```
- for Linux
```bash
source myenv/bin/activate
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
│   /home/vodaiphuoc/Projects/OCR_Thingy_dev/inference_server/run_with_vllm.py
├── 🔨 Created mount /home/vodaiphuoc/Projects/OCR_Thingy_dev/commons
└── 🔨 Created web function serve => 
    https://phuocvodn98--inference-server-internvl3-serve.modal.run
✓ App deployed in 3.831s! 🎉

View Deployment: 
https://modal.com/apps/phuocvodn98/main/deployed/Inference-server-internVL3
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