ssh -t bosco@216.153.60.196 "cd rs/rshow; /home/bosco/mambaforge/envs/rs/bin/pip install -e ."
ssh -t bosco@216.153.60.196 "sudo service supervisor restart"
