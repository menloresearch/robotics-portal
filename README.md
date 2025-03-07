# Portal Simulation / Uranus Notebook???

## Installation step

Change directory into the `app/frontend` and install the dependencies:

```bash
cd app/frontend
bun install
```

Then, you can run:

```bash
bun dev
```

To start the production server. Alternatively, feel free to use any JavaScript runtime that you want to spin up the frontend.

To spin up the server, make sure that you computer has a GPU, this is because as of now we have not optimised for UX yet, but in practice it could also run on a CPU.

Navigate to `app/backend` and start the server as follow:

```bash
python app.py
```

For now, please resolve dependencies as you encounter error as we have not had the time to create a `requirements.txt` yet.
