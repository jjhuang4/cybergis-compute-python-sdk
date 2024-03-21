import os
import math
import ipywidgets as widgets
from ipyfilechooser import FileChooser
from IPython.display import Markdown, display, clear_output
from .MarkdownTable import MarkdownTable  # noqa
import requests
import datetime
import geopandas as gpd
import webbrowser


class UI:
    """
    UI class.
    Note:
        Many UI elements use an internal `on_change`
        function or `on_click` function. If you click the `[source]`
        next to the function, it will give that information.
    Attributes:
        compute: Instance of CyberGISCompute
        style (dict): Style of each widget (specifically width)
        layout (obj): Widget layout
        jobs (list): Jobs being managed currently
        hpcs (list): HPCs the jobs are being submitted to
        defaultJobName (string): Name that jobs are given by default
        defaultRemoteResultFolder (string): Default remote location
            that results are saved to.
        defaultDataFolder (string): Default folder that data will be saved to
        slurm_configs (list): Default configurations for slurm
        slurm_integer_configs (list): Slurm configurations that can
            be stored as integers
        slurm_integer_storage_unit_config (list): Slurm configurations
            related to storage
        slurm_integer_time_unit_config (list): Slurm configurations
            related to time units
        slurm_integer_none_unit_config (list): Slurm configurations
            related to units other than time
        slurm_string_option_configs (list): Slurm configurations
            for string operations
        globus_filename (string): Output filename submitted to
            Globus (set when entered by the user)
        jupyter_globus (dict): Information about where the output data will be
            stored (container_home_path, endpoint, root_path)
    """
    def __init__(self, compute, defaultJobName="hello_world", defaultDataFolder="./", defaultRemoteResultFolder=None):
        self.compute = compute
        self.style = {'description_width': 'auto'}
        self.layout = widgets.Layout(width='60%')
        self.jobs = None
        self.hpcs = None
        self.defaultJobName = defaultJobName
        df = defaultRemoteResultFolder
        if df is not None:
            self.defaultRemoteResultFolder = df if df[0] == '/' else '/' + df
        self.defaultDataFolder = defaultDataFolder
        # slurm configs
        self.slurm_configs = [
            'num_of_node', 'num_of_task', 'time',
            'cpu_per_task', 'memory_per_cpu', 'memory_per_gpu',
            'memory', 'gpus', 'gpus_per_node', 'gpus_per_socket',
            'gpus_per_task', 'partition']
        self.slurm_integer_configs = [
            'num_of_node', 'num_of_task', 'time', 'cpu_per_task',
            'memory_per_cpu', 'memory_per_gpu', 'memory', 'gpus',
            'gpus_per_node', 'gpus_per_socket', 'gpus_per_task']
        self.slurm_integer_storage_unit_config = ['memory_per_cpu', 'memory_per_gpu', 'memory']
        self.slurm_integer_time_unit_config = ['time']
        self.slurm_integer_none_unit_config = [
            'cpu_per_task', 'num_of_node', 'num_of_task', 'gpus',
            'gpus_per_node', 'gpus_per_socket', 'gpus_per_task']
        self.slurm_string_option_configs = ['partition']
        self.globus_filename = None
        self.jupyter_globus = None

    def render(self):
        """
        Render main UI by initializing, rendering,
        and displaying each component
        """
        self.init()
        self.renderComponents()
        divider = Markdown('***')
        # render main UI
        # 1. job template
        job_config = widgets.Output()
        with job_config:
            display(Markdown('# Welcome to CyberGIS-Compute'))
            display(Markdown('A scalable middleware framework for enabling high-performance and data-intensive geospatial research and education on CyberGIS-Jupyter. [Click here for documentation.](https://cybergis.github.io/cybergis-compute-python-sdk/index.html)'))
            display(divider)
            display(Markdown('**Your CyberGIS-Compute Username:** ' + str(self.compute.username)))
            self.renderAnnouncements()
            display(self.jobTemplate['output'])
            display(self.description['output'])
            display(self.computingResource['output'])
            display(self.slurm['output'])
            display(self.param['output'])
            display(self.uploadData['output'])
            display(self.email['output'])
            display(self.name['output'])
            display(self.submit['output'])
            display(self.submitNew['output'])

        # 2. job status
        job_status = widgets.Output()
        with job_status:
            display(self.resultStatus['output'])
            display(self.resultCancel['output'])
            display(divider)
            display(Markdown('## 📋 job events (live refresh)'))
            display(self.resultEvents['output'])
            display(divider)
            display(Markdown('## 📋 job logs'))
            display(self.resultLogs['output'])

        # 3. download
        download = widgets.Output()
        with download:
            display(self.download['output'])

        # 4. your jobs
        job_refresh = widgets.Output()
        with job_refresh:
            display(self.recently_submitted['output'])
            display(self.load_more['output'])

        # 5. your folders
        user_folders = widgets.Output()
        with user_folders:
            display(self.folders['output'])

        # 6. extra script execution post run
        script_exec = widgets.Output()
        with script_exec:
            display(self.scripts['output'])

        # assemble into tabs
        self.tab = widgets.Tab(children=[
            job_config,
            job_status,
            download,
            job_refresh,
            user_folders,
            script_exec
        ])
        self.tab.set_title(0, 'Job Configuration')
        self.tab.set_title(1, 'Your Job Status')
        self.tab.set_title(2, 'Download Job Result')
        self.tab.set_title(3, 'Your Jobs')
        self.tab.set_title(4, 'Past Results')
        self.tab.set_title(5, 'Post Run Scripts')
        display(self.tab)

    def renderComponents(self):
        """
        Render each section of the UI
        """
        self.renderJobTemplate()
        self.renderDescription()
        self.renderComputingResource()
        self.renderSlurm()
        self.renderEmail()
        self.renderNaming()
        self.renderSubmit()
        self.renderParam()
        self.renderUploadData()
        self.renderResultStatus()
        self.renderResultCancel()
        self.renderResultEvents()
        self.renderResultLogs()
        self.renderDownload()
        self.renderRecentlySubmittedJobs()
        self.renderLoadMore()
        self.renderSubmitNew()
        self.renderFolders()
        self.renderScripts()

    # components
    def renderAnnouncements(self):
        """
        Displays announcements if the announcement route exists and there are any
        """
        try:
            announcement = self.compute.client.request('GET', '/announcement')["announcements"]
            if (len(announcement) > 0):
                display(Markdown('## Announcements'))
                for i in range(len(announcement)):
                    display(Markdown('### Message ' + str(i + 1) + ':'))
                    display(Markdown('Message: ' + announcement[i]["message"]))
                    display(Markdown('Posted by: ' + announcement[i]["poster"] + " at " + announcement[i]["time_stamp"]))
                display(Markdown("***"))
        except:
            pass

    def renderJobTemplate(self):
        """
        Display a dropdown of jobs to run.
        Update jobTemplate when the dropdown changes.
        """
        if self.jobTemplate['output'] is None:

            self.jobTemplate['output'] = widgets.Output()
        # create components
        self.jobTemplate['dropdown'] = widgets.Dropdown(
            options=[i for i in self.jobs], value=self.jobName,
            description='📦 Job Templates:',
            style=self.style,
            layout=self.layout)
        self.jobTemplate['dropdown'].observe(self.onJobDropdownChange(), names=['value'])
        with self.jobTemplate['output']:
            display(self.jobTemplate['dropdown'])

    def renderDescription(self):
        """
        Display information about the job (job name, job description,
        HPC name, HPC description, estimated runtime)
        """
        if self.description['output'] is None:
            self.description['output'] = widgets.Output()

        self.description['job_description'] = Markdown('**' + self.jobName + ' Job Description:** ' + self.job['description'])
        self.description['computing_resource_description'] = Markdown('**' + self.hpcName + ' HPC Description**: ' + self.hpc['description'])
        self.description['estimated_runtime'] = Markdown(
            '**Estimated Runtime:** ' + self.job['estimated_runtime'])
        with self.description['output']:
            display(
                self.description['job_description'],
                self.description['computing_resource_description'],
                self.description['estimated_runtime'])

    def renderComputingResource(self):
        """
        Display computing resources in a dropdown for the user to select
        """
        if self.computingResource['output'] is None:
            self.computingResource['output'] = widgets.Output()
        # create components
        self.computingResource['dropdown'] = widgets.Dropdown(
            options=[i for i in self.job['supported_hpc']],
            value=self.hpcName,
            description='🖥 Computing Resource:',
            style=self.style,
            layout=self.layout)
        self.computingResource['accordion'] = widgets.Accordion(
            children=(self.computingResource['dropdown'], ),
            selected_index=None)
        self.computingResource['accordion'].set_title(
            0, 'Computing Resource')
        self.computingResource['dropdown'].observe(
            self.onComputingResourceDropdownChange(), names=['value'])
        with self.computingResource['output']:
            display(self.computingResource['accordion'])

    def renderEmail(self):
        """
        Displays a checkbox that lets the user receive an email
        on job status and input their email.
        """
        if self.email['output'] is None:
            self.email['output'] = widgets.Output()
        # create components
        self.email['checkbox'] = widgets.Checkbox(
            description='receive email on job status? ',
            value=False, style=self.style)
        self.email['text'] = widgets.Text(
            placeholder='example@illinois.edu', style=self.style)
        self.email['hbox'] = widgets.HBox(
            [self.email['checkbox'], self.email['text']])
        with self.email['output']:
            display(self.email['hbox'])

    def renderNaming(self):
        """
        Displays a box to toggle naming the job being submitted
        and provides a text entry for the user to input the name
        """
        if self.name['output'] is None:
            self.name['output'] = widgets.Output()
        # create components
        self.name['checkbox'] = widgets.Checkbox(
            description='Set a name for this job? ',
            value=False, style=self.style)
        self.name['text'] = widgets.Text(
            placeholder='Type job name here', style=self.style)
        self.name['hbox'] = widgets.HBox(
            [self.name['checkbox'], self.name['text']])
        with self.name['output']:
            display(Markdown("Please note that the naming feature only allows for names made up of letters, numbers, and the characters ' . ' and ' _ '. Other characters will be removed from your input."))
            display(self.name['hbox'])

    def renderSlurm(self):
        """
        Configures Slurm input rules (default value, min, m),
        allows the user to input custom input rules if they want.
        """
        if self.slurm['output'] is None:
            self.slurm['output'] = widgets.Output()
        # check if necessary to render
        if self.job['slurm_input_rules'] == {}:
            return
        # create components
        self.slurm['description'] = widgets.Label(value='All configs are optional. Please refer to Slurm official documentation at 🔗 https://slurm.schedmd.com/sbatch.html')
        # settings
        for i in self.slurm_configs:
            if i not in self.job['slurm_input_rules']:
                self.slurm[i] = None
                continue
            config = self.job['slurm_input_rules'][i]
            if i in self.slurm_integer_configs:
                default_val = config['default_value']
                max_val = config['max']
                min_val = config['min']
                step_val = config['step']
                unit = config['unit']
                description = i + ' (' + unit + ')' if unit != 'None' else i
                self.slurm[i] = widgets.IntSlider(
                    value=default_val,
                    min=min_val,
                    max=max_val,
                    step=step_val,
                    disabled=False,
                    continuous_update=False,
                    orientation='horizontal',
                    readout=True,
                    readout_format='d',
                    description=description,
                    style=self.style, layout=self.layout
                )
            if i in self.slurm_string_option_configs:
                default_val = config['default_value']
                options = config['options']
                self.slurm[i] = widgets.Dropdown(
                    options=options,
                    value=default_val,
                    description=i,
                    style=self.style
                )

        w = []
        for i in self.slurm_configs:
            if self.slurm[i] is not None:
                w.append(self.slurm[i])
        self.slurm['vbox'] = widgets.VBox(w)

        # settings end
        self.slurm['accordion'] = widgets.Accordion(children=(widgets.VBox(children=(self.slurm['description'], self.slurm['vbox'])),), selected_index=None)
        self.slurm['accordion'].set_title(0, 'Slurm Computing Configurations')
        with self.slurm['output']:
            display(self.slurm['accordion'])

    def renderUploadData(self):
        """
        Lets the user select the upload data location from a file chooser.
        """
        if self.uploadData['output'] is None:
            self.uploadData['output'] = widgets.Output()
        # check if necessary to render
        if not self.job['require_upload_data']:
            return
        # render all
        self.uploadData['selector'] = FileChooser(
            self.defaultDataFolder,
            select_default=True if self.defaultDataFolder != './' else False)
        self.uploadData['selector'].show_only_dirs = True
        self.uploadData['selector'].title = 'Job requires upload data.' + 'Please select a folder to upload'
        self.uploadData['accordion'] = widgets.Accordion(children=(self.uploadData['selector'], ), selected_index=None)
        self.uploadData['accordion'].set_title(0, 'Upload Data')
        with self.uploadData['output']:
            display(self.uploadData['accordion'])

    def renderParam(self):
        """
        Displays input areas for the job parameters
        """
        if self.param['output'] is None:
            self.param['output'] = widgets.Output()
        # check if necessary to render
        if self.job['param_rules'] == {}:
            return
        # clear config
        for i in self.param:
            if i != 'output':
                self.param[i] = None

        # render param
        for i in self.job['param_rules']:
            config = self.job['param_rules'][i]

            if config['type'] == 'integer':
                if self.input_params is not None and i in self.input_params.keys():
                    default_val = self.input_params[i]
                else:
                    default_val = config['default_value']
                max_val = config['max']
                min_val = config['min']
                step_val = config['step']
                description = i
                self.param[i] = widgets.IntSlider(
                    value=default_val,
                    min=min_val,
                    max=max_val,
                    step=step_val,
                    disabled=False,
                    continuous_update=False,
                    orientation='horizontal',
                    readout=True,
                    readout_format='d',
                    description=description,
                    style=self.style, layout=self.layout
                )
            if config['type'] == 'string_option':
                if self.input_params is not None and i in self.input_params.keys() and self.input_params[i] in config['options']:
                    default_val = self.input_params[i]
                else:
                    default_val = config['default_value']
                options = config['options']
                self.param[i] = widgets.Dropdown(
                    options=options,
                    value=default_val,
                    description=i,
                    style=self.style
                )
            if config['type'] == 'string_input':
                if self.input_params is not None and i in self.input_params.keys():
                    default_val = self.input_params[i]
                else:
                    default_val = config['default_value']
                self.param[i] = widgets.Text(
                    description=i, value=default_val, style=self.style)

        # render all
        self.param['vbox'] = widgets.VBox([self.param[i] for i in self.job['param_rules']])
        # settings end
        self.param['accordion'] = widgets.Accordion(children=(self.param['vbox'], ), selected_index=None)
        self.param['accordion'].set_title(0, 'Input Parameters')
        with self.param['output']:
            display(self.param['accordion'])

    def renderSubmit(self):
        """
        Render submit button. If the job has been submitted,
        display that, otherwise display the submit button.
        """
        if self.submit['output'] is None:
            self.submit['output'] = widgets.Output()
        if self.submit['alert_output'] is None:
            self.submit['alert_output'] = widgets.Output()
        # create components
        if self.submitted:
            self.submit['button'] = widgets.Button(
                description="Job Submitted ✅", disabled=True)
        else:
            self.submit['button'] = widgets.Button(description="Submit Job")
        self.submit['button'].on_click(self.onSubmitButtonClick())
        with self.submit['output']:
            display(self.submit['alert_output'])
            display(self.submit['button'])

    def renderSubmitNew(self):
        """
        Render submit new button, which allows the user to return the SDK to a pre-submission state so they can submit successive jobs.
        """
        if self.submitNew['output'] is None:
            self.submitNew['output'] = widgets.Output()
        if self.submitted:
            self.submitNew['button'] = widgets.Button(description="Submit New Job")
        else:
            self.submitNew['button'] = None

        with self.submitNew['output']:
            if self.submitted:
                self.submitNew['button'] = widgets.Button(description="Submit New Job")
                display(self.submitNew['button'])
            else:
                self.submitNew['button'] = None
        if self.submitNew['button'] is not None:
            self.submitNew['button'].on_click(self.onSubmitNewButtonClick())

    def renderDownload(self):
        """
        Creates the components of the download section
        """
        if self.download['output'] is None:
            self.download['output'] = widgets.Output()
        if self.download['alert_output'] is None:
            self.download['alert_output'] = widgets.Output()
        if self.download['result_output'] is None:
            self.download['result_output'] = widgets.Output()
        # create components
        if self.jobFinished:
            result_folder_content = self.compute.job.result_folder_content()
            # push default value to front
            try:
                result_folder_content.insert(
                    0, result_folder_content.pop(
                        result_folder_content.index(
                            self.defaultRemoteResultFolder)))
            except Exception:
                result_folder_content
            if len(result_folder_content) == 0:
                raise Exception('failed to get result folder content')
            self.download['dropdown'] = widgets.Dropdown(
                options=result_folder_content, value=result_folder_content[0],
                description='select file/folder')
            self.download['button'] = widgets.Button(description="Download")
            self.download['button'].on_click(self.onDownloadButtonClick())
        else:
            self.download['button'] = widgets.Button(
                description="Download", disabled=True)

        with self.download['output']:
            if self.jobFinished:
                display(Markdown('# ☁️ Download Job Output Files'))
                display(self.download['alert_output'])
                display(self.download['result_output'])
                display(self.download['dropdown'])
            else:
                display(Markdown('# ⏳ Waiting for Job to Finish...'))
            display(self.download['button'])

    def renderResultStatus(self):
        """
        Display the status of the job.
        """
        if self.resultStatus['output'] is None:
            self.resultStatus['output'] = widgets.Output()

        if not self.submitted:
            with self.resultStatus['output']:
                display(Markdown('# 😴 No Job to Work On'))
                display(Markdown('you need to submit your job first'))
            return

        with self.resultStatus['output']:
            display(Markdown('# ✌️ Your Job is Here!'))
            self.compute.job.status()
        return

    def renderResultCancel(self):
        if self.resultCancel['output'] is None:
            self.resultCancel['output'] = widgets.Output()
        with self.resultCancel['output']:
            cancelText = """<p>1. Press the stop button in the top bar of your Jupyter notebook <b>twice</b>. Please note that errors will appear on the user interface. While your logs will stop updating, <b>your job is still running</b>.</p>

<p>2. Create a new code block below the UI.</p>

<p>3. Enter this command is your code block and press run:&nbsp;<em>cybergis.cancel_job()</em></p>

<p>4. You should see a message displaying that your job has been canceled. Success!</p>"""
            cancelExp = widgets.Accordion(children=(widgets.HTML(value=cancelText), ), selected_index=None)
            cancelExp.set_title(0, "How to cancel a job")
            display(cancelExp)
        return

    def renderResultEvents(self):
        """
        Display any events that occured while the job was being processed.
        """
        if self.resultEvents['output'] is None:
            self.resultEvents['output'] = widgets.Output()
        if not self.submitted:
            return
        with self.resultEvents['output']:
            self.compute.job.events()
        return

    def renderResultLogs(self):
        """
        Display when the job is finished and
        rerender the download section when it is.
        """
        if self.resultLogs['output'] is None:
            self.resultLogs['output'] = widgets.Output()
        if not self.submitted:
            return
        with self.resultLogs['output']:
            self.compute.job.logs()
            self.tab.set_title(2, '✅ Download Job Result')
            display(Markdown('***'))
            display(Markdown('## ✅ your job completed'))
            self.jobFinished = True
            self.rerender(['download'])
        with self.scripts['output']:
            self.rerender(['scripts'])
        return

    def search(self):  # function for searching from directory that post job-run scripts recently outputted to
        """
        Helper function to search directory and all subdirectories recursively
        """
        def search_dir(dir, data, file_ext_list):
            for entry in os.listdir(dir):  # check subdirectories
                path = os.path.join(dir, entry)
                if os.path.isdir(path):
                    data = search_dir(path, data, file_ext_list)
                elif os.path.isfile(path):
                    file_name, file_ext = os.path.splitext(path)
                    if file_ext.lower() not in file_ext_list:
                        continue
                    else:
                        # check for recency (file was created in last 30 minutes)
                        c = datetime.datetime.fromtimestamp(os.path.getctime(path))
                        if datetime.datetime.now() - c < datetime.timedelta(minutes=30):
                            data.append(path)
            return data
        """
        Helper function to run raw script and get output data files
        """
        def search_files(d=os.getcwd()):
            data_files = []
            print(f"Searching for data files in: {d}")
            # get all files that can be viewed and operated on as dataframes
            data_files = search_dir(d, data_files, ['.csv', '.shp', '.geojson'])
            if not data_files:
                display(Markdown(' No recently created compatible filetypes to view'))
            return data_files
        """
        Helper function to search for output html files
        """
        def search_html(d=os.getcwd()):
            html_files = []
            print(f"Searching for html files in: {d}")
            html_files = search_dir(d, html_files, ['.html'])
            if not html_files:
                display(Markdown(' No recently created html files to view'))
            return html_files
        dest = self.scripts['script_destination']
        return search_files(dest), search_html(dest)

    def renderScripts(self):
        if self.scripts['output'] is None:
            self.scripts['output'] = widgets.Output()
        with self.scripts['output']:
            if self.jobFinished is False:
                display(Markdown('# ⏳ Waiting for Job to Finish...'))
            else:
                display(Markdown(" Checking job manifest for additional scripts... "))
                dest = self.compute.recentDownloadPath  # if recently downloaded, make destination recent download folder
                if dest is None:
                    print("!!! Cannot read in recent download path, destination now current working directory")
                    dest = os.getcwd()

                scripts = []
                for key, value in self.job.items():  # iterate through manifest to locate post_run_scripts
                    if key == "post_run_scripts":
                        if value is not None:  # if raw script url exists
                            scripts.append(value)
                if scripts is not None:
                    print("Found extra scripts to run post job execution, would you like to run?")
                    print("Raw scripts: ")
                    for raw in scripts:
                        print(raw)
                    self.scripts['button'] = widgets.Button(description="Run script")
                    self.scripts['script_raw'] = scripts[0]
                    self.scripts['script_destination'] = dest
                    self.scripts['button'].on_click(self.onScriptRunButtonClick())
                    display(self.scripts['button'])
                if self.script_executed:  # if post job script was recently executed:
                    script_output_files, html_files = self.search()
                    if script_output_files is None and html_files is None:
                        print("No files downloaded from script execution")
                        return
                    if html_files is not None:
                        self.scripts['html_dropdown'] = widgets.Dropdown(
                            options=html_files, value=html_files[0],
                            description='Select html file to open')
                        display(self.scripts['html_dropdown'])
                        self.scripts['html_button'] = widgets.Button(description="Display html in web browser")
                        self.scripts['html_button'].on_click(self.onHtmlButtonClick())
                        display(self.scripts['html_button'])
                    if script_output_files is not None:
                        self.scripts['script_dropdown'] = widgets.Dropdown(
                            options=script_output_files, value=script_output_files[0],
                            description='Select data file to display')
                        display(self.scripts['script_dropdown'])
                        self.scripts['visual_button'] = widgets.Button(description="Visualize geospatial file")
                        self.scripts['visual_button'].on_click(self.onVisualizeButtonClick())
                        display(self.scripts['visual_button'])

    def onScriptRunButtonClick(self):
        """
        Helper function to run script from url and send output files to specified destination directory
        """
        def run_script(destination, url):
            with self.scripts['output']:
                print(f"Running script from: {url}")
                os.chdir(destination)
                print(f"Sending all output files to: {os.getcwd()}")
                r = requests.get(url)
                if r.status_code == 200:
                    try:
                        exec(r.text, globals())
                    except Exception as e:
                        print("Download successful, but running file led to error")
                        print(e)
                        return
                return

        def show_files(out_dir):
            with self.scripts['output']:
                # For printing out directory in testing
                try:
                    output = os.listdir(out_dir)
                    if output:
                        print(f"\nContents of destination directory '{out_dir}':")
                        for file in output:
                            print(file)
                    else:
                        print(f"The directory '{out_dir}' is empty.")
                except Exception as e:
                    print(f"Unable to access directory {out_dir} / directory not found")
                    print(e)

        def on_click(change):
            self.script_executed = True
            dest = self.scripts['script_destination']
            value = self.scripts['script_raw']
            run_script(dest, value)
            show_files(dest)
            self.rerender(['scripts'])
        return on_click

    def onVisualizeButtonClick(self):
        """
        Helper function to convert file into geodataframe
        """
        def to_geofile(geo_filepath):
            ext = os.path.splitext(geo_filepath)[1]
            if ext not in ['.shp', '.geojson']:
                print("Not a valid geodataframe file")
                return
            gdf = gpd.read_file(geo_filepath)
            try:
                gdf = gdf.to_crs(epsg=4326)
            except Exception as e:
                gdf = gdf.set_crs("EPSG:4326", allow_override=False)
                print(e)
            return gdf
        """
         Helper function to display a geodataframe using explore() function
        """
        def geo_vis(gdf):
            map = gdf.explore(tiles='OpenStreetMap')
            map.save("map_visualization2.html")
            map_html = map._repr_html_()  # convert explore() map to html string
            iframe = widgets.HTML(
                value=map_html,
                placeholder='Loading map...',
                description='Map:',
            )
            return iframe

        def on_click(change):
            with self.scripts['output']:
                self.rerender(['scripts'])
                geo_filepath = self.scripts['script_dropdown'].value
                display(Markdown("Processing file..."))
                print("Converting to geodataframe")
                gdf = to_geofile(geo_filepath)
                print("Showing map display")
                iframe = geo_vis(gdf)
                display(iframe)
        return on_click
    
    def onHtmlButtonClick(self):
        def on_click(change):
            with self.scripts['output']:
                self.rerender(['scripts'])
                html_path = self.scripts['html_dropdown'].value
                if os.name == 'nt': # Windows
                    file_path = 'file:///' + os.path.abspath(html_path)
                else: # MacOS or Linux
                    file_path = 'file://' + os.path.abspath(html_path)
                # Open file in the default web browser
                webbrowser.open_new_tab(file_path)
        return on_click

    def renderFolders(self):
        """
        Display a user's folders with ability to download and rename them
        """
        folders = self.compute.client.request('GET', '/folder', {'jupyterhubApiToken': self.compute.jupyterhubApiToken})
        if self.folders['output'] is None:
            self.folders['output'] = widgets.Output()
        with self.folders['output']:
            display(Markdown("We will do our best to keep this data for 90 days, but cannot guarantee it won’t be deleted sooner."))
            display(Markdown("Please note that the renaming feature only allows for names made up of letters, numbers, and the characters ' . ' and ' _ '. Other characters will be removed from your input."))
            pageNum = self.folderPage
            numFolders = self.foldersPerPage
            firstFolder = pageNum * numFolders
            lastFolder = firstFolder + numFolders
            if (lastFolder >= len(folders["folder"])):
                lastFolder = len(folders["folder"])
            display(Markdown('<br> **Showing folders ' + str(firstFolder + 1) + ' to ' + str(lastFolder) + ' of ' + str(len(folders["folder"])) + ' for ' + self.compute.username.split('@', 1)[0] + '**'))
            backButton = widgets.Button(description="Previous Page")
            nextButton = widgets.Button(description="Next Page")
            pageButtons = widgets.HBox([backButton, nextButton])
            backButton.on_click(self.onPrevPageButton())
            nextButton.on_click(self.onNextPageButton(len(folders["folder"])))
            display(pageButtons)
            listNames = []
            for i in folders["folder"]:
                if i['name'] is not None:
                    listNames.append(i['name'])
            listNames = [*set(listNames)]
            for i in list(reversed(folders["folder"]))[firstFolder:lastFolder]:
                headers = ['id', 'name', 'hpc', 'userId', 'isWritable', 'createdAt', 'updatedAt', 'deletedAt']
                data = [[]]
                for j in headers:
                    data[0].append(i[j])
                display(Markdown(MarkdownTable.render(data, headers)))
                self.folders['button'][i['id']] = widgets.Button(description="Download Results")
                display(self.folders['button'][i['id']])
                self.folders['button'][i['id']].on_click(self.onFolderDownloadButtonClick(i))
                """ Renaming UI """
                renameButton = widgets.Button(description="Rename Job")
                nameSelect = widgets.Combobox(placeholder='Select new name', options=listNames, description='Enter Name:', ensure_option=False, disabled=False)
                renameWidgets = widgets.HBox([renameButton, nameSelect])
                renameButton.on_click(self.onRenameJobButton(i, nameSelect))
                nameSelect.on_submit(self.onRenameJobButton(i, nameSelect))
                display(renameWidgets)
            display(Markdown('<br> **Showing folders ' + str(firstFolder + 1) + ' to ' + str(lastFolder) + ' of ' + str(len(folders["folder"])) + '**'))
            display(pageButtons)

    def renderRecentlySubmittedJobs(self):
        """
        Display the jobs most recently submitted by the logged in user, allows user to restore these jobs.
        """
        if self.recently_submitted['output'] is None:
            self.recently_submitted['output'] = widgets.Output()
            jobs = self.compute.client.request('GET', '/user/job', {'jupyterhubApiToken': self.compute.jupyterhubApiToken})
        with self.recently_submitted['output']:
            display(Markdown('**Recently Submitted Jobs for ' + self.compute.username.split('@', 1)[0] + '**'))
            jobs = self.compute.client.request('GET', '/user/job', {'jupyterhubApiToken': self.compute.jupyterhubApiToken})
            if len(jobs['job']) < self.recently_submitted['job_list_size']:
                self.recently_submitted['job_list_size'] = len(jobs['job'])
            for i in range(len(jobs['job']) - 1, len(jobs['job']) - self.recently_submitted['job_list_size'] - 1, -1):
                job = self.compute.get_job_by_id(jobs['job'][i]['id'], verbose=False)
                jobDetails = jobs['job'][i]
                job._print_job_formatted(jobDetails)
                if self.refreshing:
                    self.recently_submitted['submit'][jobs['job'][i]['id']] = widgets.Button(description="🔁 Loading", disabled=True)
                else:
                    self.recently_submitted['submit'][jobs['job'][i]['id']] = widgets.Button(description="Restore")
                display(self.recently_submitted['submit'][jobDetails['id']])
                display(Markdown("<br>"))
        for i in self.recently_submitted['submit'].keys():
            self.recently_submitted['submit'][i].on_click(self.onJobEntryButtonClick(i))

    def renderLoadMore(self):
        """
        Renders a button to load more recently submitted jobs.
        """
        if self.load_more['output'] is None:
            self.load_more['output'] = widgets.Output()
            self.load_more['load_more'] = widgets.Button(description="Load More")
        with self.load_more['output']:
            if self.refreshing:
                self.load_more['load_more'] = widgets.Button(description="🔁 Loading", disabled=True)
            else:
                self.load_more['load_more'] = widgets.Button(description="Load More")
            display(self.load_more['load_more'])
        self.load_more['load_more'].on_click(self.onLoadMoreClick())

    # events
    def onDownloadButtonClick(self):
        def on_click(change):
            """
            Download the output data to the specified path
            and display the location.
            """
            if self.downloading:
                self.download['alert_output'].clear_output(wait=True)
                with self.download['alert_output']:
                    display(
                        Markdown('⚠️ download process is running in background...'))
                    return

            with self.download['result_output']:
                self.refreshing = True
                self.recently_submitted['output'].clear_output()
                self.load_more['output'].clear_output()
                self.renderRecentlySubmittedJobs()
                self.renderLoadMore()
                self.download['alert_output'].clear_output(wait=True)
                self.downloading = True
                localEndpoint = self.jupyter_globus['endpoint']
                """ Ensures file should be saved with name and has a non-null value """
                if self.name['checkbox'].value and self.name['text'].value is not None and self.name['text'].value != "":
                    filename = self.makeNameSafe(self.name['text'].value) + '_' + self.globus_filename
                else:
                    filename = self.globus_filename
                localPath = os.path.join(self.jupyter_globus['root_path'], filename)
                self.compute.job.download_result_folder_by_globus(remotePath=self.download['dropdown'].value, localEndpoint=localEndpoint, localPath=localPath)
                print('please check your data at your root folder under "' + filename + '"')
                self.compute.recentDownloadPath = os.path.join(self.jupyter_globus['container_home_path'], filename)
                self.downloading = False
                self.refreshing = False
                self.recently_submitted['output'].clear_output()
                self.load_more['output'].clear_output()
                self.renderRecentlySubmittedJobs()
                self.renderLoadMore()

        return on_click

    def onSubmitNewButtonClick(self):
        def on_click(change):
            self.submitted = False
            self.rerender(['resultStatus', 'resultEvents', 'resultLogs', 'submit'])
            self.submitNew['output'].clear_output()
            self.tab.set_title(2, 'Download Job Result')
            self.renderSubmitNew()
        return on_click

    def onSubmitButtonClick(self):
        def on_click(change):
            """
            Submit the job, then rerender the result status,
            result events, result logs, and submit button.
            """
            if self.submitted:
                return
            with self.submit['alert_output']:
                clear_output(wait=True)

            self.compute.login()
            localDataFolder = None
            data = self.get_data()
            if data['computing_resource'] != 'local_hpc':
                self.jupyter_globus = self.compute.get_user_jupyter_globus()
            if self.job['require_upload_data']:
                dataPath = self.uploadData['selector'].selected
                if dataPath is None:
                    with self.submit['alert_output']:
                        display(Markdown('⚠️ please select a folder before upload...'))
                        return
                else:
                    dataPath = dataPath.replace(self.jupyter_globus['container_home_path'].strip('/'), '')
                    dataPath = os.path.join(self.jupyter_globus['root_path'], dataPath.strip('/'))
                    localDataFolder = {
                        'type': 'globus',
                        'endpoint': self.jupyter_globus['endpoint'],
                        'path': dataPath
                    }
            try:
                self.compute.job = self.compute.create_job(hpc=data['computing_resource'], verbose=False)
            except Exception as e:
                print("There was an exception while submitting the job: " + str(e))
                if "Not authorized for HPC" in str(e):  # TODO: we should create a specific exception rather than checking the message
                    with self.submit['alert_output']:
                        display(Markdown("<b><font color='red'>You are not authorized to submit jobs to this HPC (" + str(data['computing_resource']) + "). Please try another HPC or contact the CyberGIS-Compute team.</b>"""))
                else:  # generic error
                    with self.submit['alert_output']:
                        display(Markdown("<b><font color='red'>There was an exception while submitting the job: " + str(e) + "</b>"))
                return
            # slurm
            slurm = data['slurm']
            if data['email'] is not None:
                slurm['mail_user'] = [data['email']]
                slurm['mail_type'] = ['FAIL', 'END', 'BEGIN']
            # param
            param = data['param']
            # download
            self.globus_filename = 'globus_download_' + self.compute.job.id
            # executable
            localExecutableFolder = {
                'type': 'git',
                'gitId': data['job_template']
            }

            # submit
            self.compute.job.set(localExecutableFolder=localExecutableFolder, localDataFolder=localDataFolder, printJob=False, param=param, slurm=slurm)
            self.compute.job.submit()
            self.tab.selected_index = 1
            self.submitted = True
            self.tab.set_title(1, '⏳ Your Job Status')
            self.rerender(['resultStatus', 'resultEvents', 'resultLogs', 'submit'])
            self.recently_submitted['output'].clear_output()
            self.load_more['output'].clear_output()
            self.submitNew['output'].clear_output()
            self.renderRecentlySubmittedJobs()
            self.renderSubmitNew()
            """ If the user has indicated the job should be named and provided a name, the produced files are named here """
            if data['name'] is not None and data['name'] != "":
                nameForFile = self.makeNameSafe(data['name'])
                jobs = self.compute.client.request('GET', '/user/job', {'jupyterhubApiToken': self.compute.jupyterhubApiToken})
                job = jobs['job'][len(jobs['job']) - 1]
                useFolder = job['remoteExecutableFolder']['id']
                self.compute.client.request('PUT', '/folder/' + useFolder, {'jupyterhubApiToken': self.compute.jupyterhubApiToken, 'name': nameForFile + '_executable'})
                useFolder = job['remoteResultFolder']['id']
                self.compute.client.request('PUT', '/folder/' + useFolder, {'jupyterhubApiToken': self.compute.jupyterhubApiToken, 'name': nameForFile + '_result'})
        return on_click

    def onJobDropdownChange(self):
        def on_change(change):
            """
            If the information in the dropdown is changed,
            modify the information in jobName, job, hpcName,
            and hpc to match. Then, rerender the description,
            computing resources, sulurn, param and upload data.
            """
            if change['type'] == 'change':
                if self.submitted:
                    return
                self.jobName = self.jobTemplate['dropdown'].value
                self.job = self.jobs[self.jobName]
                self.hpcName = self.job['default_hpc']
                self.hpc = self.hpcs[self.hpcName]
                self.rerender(
                    [
                        'description', 'computingResource',
                        'slurm', 'param', 'uploadData'])
        return on_change

    def onComputingResourceDropdownChange(self):
        def on_change(change):
            """
            If the information in the computing resources
            dropdown is changed, update the hpcName and hpc,
            then rerender the description, computing resources,
            sulurn, param and upload data.
            """
            if change['type'] == 'change':
                if self.submitted:
                    return
                self.hpcName = self.computingResource['dropdown'].value
                self.hpc = self.hpcs[self.hpcName]
                self.rerender(['description', 'slurm', 'param', 'uploadData'])
                self.submit['alert_output'].clear_output()  # clear any errors from previous job
        return on_change

    def onLoadMoreClick(self):
        def on_click(change):
            """
            Increase the number of recently submitted jobs being displayed by five and rerender teh recently subsmitted and load more attributes.
            """
            self.recently_submitted['job_list_size'] += 5
            self.recently_submitted['output'].clear_output()
            self.load_more['output'].clear_output()
            self.renderRecentlySubmittedJobs()
            self.renderLoadMore()
        return on_click

    def onJobEntryButtonClick(self, job_id):
        def on_click(change):
            """
            When the restore job button is pressed, restore the state of the UI to when that job was just submitted so the user can read logs and download data.
            """
            job = self.compute.get_job_by_id(job_id, verbose=False)
            self.compute.job = job
            self.jupyter_globus = self.compute.get_user_jupyter_globus()
            self.globus_filename = 'globus_download_' + self.compute.job.id
            self.tab.selected_index = 1
            self.submitted = True
            self.rerender(['resultStatus', 'resultEvents', 'resultLogs', 'submit', 'submitNew'])
            self.recently_submitted['output'].clear_output()
            self.load_more['output'].clear_output()
            self.renderRecentlySubmittedJobs()
            self.renderLoadMore()
            self.refreshing = False
        return on_click

    def onFolderDownloadButtonClick(self, folder):
        def on_click(change):
            jupyter_globus = self.compute.get_user_jupyter_globus()
            localEndpoint = jupyter_globus['endpoint']
            """ Tries using name, and if no name is provided downloads folder without name information """
            try:
                localPath = os.path.join(jupyter_globus['root_path'], self.makeNameSafe(folder["name"]) + "_globus_download_" + folder["id"])
            except:
                localPath = os.path.join(jupyter_globus['root_path'], "globus_download_" + folder["id"])
            self.compute.client.request('POST', '/folder/' + folder["id"] + '/download/globus-init', {
                "jupyterhubApiToken": self.compute.jupyterhubApiToken,
                "fromPath": '/',
                "toPath": localPath,
                "toEndpoint": localEndpoint
            })
        return on_click

    def onRenameJobButton(self, folder, wdgt):
        def on_click(change):
            newName = self.makeNameSafe(wdgt.value)
            self.compute.client.request('PUT', '/folder/' + folder["id"], {'jupyterhubApiToken': self.compute.jupyterhubApiToken, 'name': newName})
            self.folders['output'].clear_output()
            self.renderFolders()
        return on_click

    def onPrevPageButton(self):
        def on_click(change):
            if (self.folderPage - 1 >= 0):
                self.folderPage -= 1
            self.folders['output'].clear_output()
            self.renderFolders()
        return on_click

    def onNextPageButton(self, totalJobs):
        def on_click(change):
            if ((self.folderPage + 1) * self.foldersPerPage < totalJobs):
                self.folderPage += 1
            self.folders['output'].clear_output()
            self.renderFolders()
        return on_click

    # helpers
    def init(self):
        """
        Initialization helper function that
        sets default arguments. Runs when the UI is rendered.
        """
        self.compute.login()

        self.jobs = self.compute.list_git(raw=True)
        self.hpcs = self.compute.list_hpc(raw=True)
        # state
        self.submitted = False
        self.jobFinished = False
        self.downloading = False
        self.refreshing = False
        self.folderPage = 0
        self.foldersPerPage = 10
        self.script_executed = False
        # components
        self.jobTemplate = {'output': None}
        self.description = {'output': None}
        self.computingResource = {'output': None}
        self.slurm = {'output': None}
        self.email = {'output': None}
        self.name = {'output': None}
        self.submit = {'output': None, 'alert_output': None}
        self.submitNew = {'output': None, 'button': None}
        self.param = {'output': None}
        self.uploadData = {'output': None}
        self.resultStatus = {'output': None}
        self.resultCancel = {'output': None}
        self.resultEvents = {'output': None}
        self.resultLogs = {'output': None}
        self.scripts = {'output': None, 'script_raw': None, 'script_destination': None}
        self.download = {'output': None, 'alert_output': None, 'result_output': None}
        self.recently_submitted = {'output': None, 'submit': {}, 'job_list_size': 5, 'load_more': None}
        self.load_more = {'output': None, 'load_more': None}
        self.folders = {'output': None, 'button': {}}
        # main
        self.tab = None
        # information
        self.jobName = self.defaultJobName
        self.job = self.jobs[self.jobName]
        self.hpcName = self.job['default_hpc']
        self.hpc = self.hpcs[self.hpcName]

    def rerender(self, components=[]):
        """
        Clears and renders the specified components
        Args:
            components (list): components to be rerendered
        """
        for c in components:
            getattr(self, c)['output'].clear_output()
        for c in components:
            cl = list(c)
            cl[0] = cl[0].upper()
            ct = ''.join(cl)
            getattr(self, 'render' + ct)()

    """ Used to ensure that folders have names with only safe characters """
    def makeNameSafe(self, text):
        keepcharacters = ('.', '_')
        return "".join(c for c in text if c.isalnum() or c in keepcharacters).rstrip()

    # data
    def get_data(self):
        """
        Get data about the job submitted (template, computing resource used,
        slurm rules, param rules, user email)

        Returns:
            dict : Information about the job submitted (template,
            computing resource used, slurm rules, param rules, user email)
        """
        out = {
            'job_template': self.jobTemplate['dropdown'].value,
            'computing_resource': self.computingResource['dropdown'].value,
            'slurm': {
                'time': '01:00:00',
                'num_of_task': 1,
                'cpu_per_task': 1
            },
            'param': {},
            'email': self.email['text'].value if self.email[
                'checkbox'].value else None,
            'name': self.name['text'].value if self.name[
                'checkbox'].value else None,
        }
        for i in self.slurm_configs:
            if self.slurm[i] is not None and i in self.job[
                    'slurm_input_rules']:
                if not self.slurm[i].value:
                    continue  # skip null value
                config = self.job['slurm_input_rules'][i]
                if i in self.slurm_integer_storage_unit_config:
                    out['slurm'][i] = str(self.slurm[i].value) + str(config['unit'])
                elif i in self.slurm_integer_time_unit_config:
                    seconds = self.unitTimeToSecond(config['unit'], self.slurm[i].value)
                    out['slurm'][i] = self.secondsToTime(seconds)
                else:
                    out['slurm'][i] = self.slurm[i].value

        for i in self.job['param_rules']:
            if i in self.param:
                out['param'][i] = self.param[i].value

        return out

    def secondsToTime(self, seconds):
        """
        Helper function that turns seconds into minutes, days, hours format
        """
        days = math.floor(seconds / (60 * 60 * 24))
        hours = math.floor(seconds / (60 * 60) - (days * 24))
        minutes = math.floor(seconds / 60 - (days * 60 * 24) - (hours * 60))

        d = '0' + str(days) if days < 10 else str(days)
        h = '0' + str(hours) if hours < 10 else str(hours)
        m = '0' + str(minutes) if minutes < 10 else str(minutes)

        if days == 0:
            if hours == 0:
                return m + ':00'
            else:
                return h + ':' + m + ':00'
        else:
            return d + '-' + h + ':' + m + ':00'

    def unitTimeToSecond(self, unit, time):
        """
        Helper function that turns time in a specific unit into seconds

        Args:
            unit (string): The unit of the time being
                passed (Minutes, Hours, or Days)
            time (int): The time in that specific unit

        Returns:
            int: the amount of time in the given unit
        """
        if unit == 'Minutes':
            return time * 60
        elif unit == 'Hours':
            return time * 60 * 60
        elif unit == 'Days':
            return time * 60 * 60 * 24
