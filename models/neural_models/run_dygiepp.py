"""
Script to run dygiepp models. Outputs into a directory structured as:

    chosen_dir_name
    |
    ├── formatted_data
    |
    ├── model_predictions
    |
    ├── allennlp_output
    |
    └── performance

Author: Serena G. Lotreck
"""
import argparse
from os.path import abspath, exists, basename, splitext
from os import makedirs, walk, listdir
import subprocess
from random import randint
from tqdm import trange


class PrefixError(Exception):
    pass


class ModelNotFoundError(Exception):
    pass


def evaluate_models(top_dir, gold_standard, out_prefix):
    """
    Runs the model evaluation script on model output.

    parameters:
        top_dir, str: path to top level output dir
        gold_standard, str: path to gold standard
        out_prefix, str: only evaluates files with this prefix

    returns: None
    """
    save_name = f'{top_dir}/performance/{out_prefix}_model_performance.csv'
    evaluate = [
        "python",
        abspath("../evaluate_model_output.py"), gold_standard, save_name,
        f'{top_dir}/model_predictions/', '--bootstrap',
        '-use_prefix', out_prefix
    ]
    subprocess.run(evaluate)



def run_model(formatted_data_path, model, dygiepp_path, top_dir,
              out_prefix):
    """
    Run a dygiepp model with a given number of random seed iterations. Replaces
    the dataset name with the correct one for the model, and saves outputs to
    model_predictions directory.

    parameters:
        formatted_data_path, str: path to formatted data
        model, str: name of the model to run
        dygiepp_path, str: path to dygiepp installation
        top_dir, str: path to top level output dir
        out_prefix, str: prefix to prepend to file names

    returns: None
    """
    # Define model shorthands used in the dataset field
    if model == 'genia-lightweight':
        dset = 'genia'
    elif model == 'scierc-lightweight':
        dset = 'scierc'
    elif model == 'ace05-relation':
        dset = 'ace05'
    else:
        dset = model

    # Replace the dataset name in input data
    replacement = f'\'.dataset="{dset}"\''
    json_replace = (
        f'jq -c {replacement} {formatted_data_path} > '
        f'{formatted_data_path}.TEMP && mv {formatted_data_path}.TEMP {formatted_data_path}'
    )  # Not the world's safest thing to just add TEMP, but couldn't get
    # $(mktemp) to work -- didn't recognize it existed in the second command,
    # and couldn't get it to work piped in the same command. It's also
    # apparently not super great to use shell=True, docs say if you use it,
    # it's the "application’s responsibility to ensure that all whitespace and
    # metacharacters are quoted appropriately to avoid shell injection vulnerabilities"
    subprocess.run(json_replace, shell=True)

    # Define the base of all output file names
    out_name = splitext(basename(formatted_data_path))[0]

    # Define output file name and location for data and allennlp output
    out_path = f'{top_dir}/model_predictions/{out_name}_{model}_predictions.jsonl'
    allen_out_path = f'{top_dir}/allennlp_output/{out_name}_{model}_allennlp_stdout.txt'

    # Run model
    if exists(f'{dygiepp_path}/pretrained/{model}.tar.gz'):
        model_run = (
            f'allennlp predict {dygiepp_path}/pretrained/{model}.tar.gz '
            f'{formatted_data_path} --predictor dygie --include-package '
            f'dygie --use-dataset-reader --output-file {out_path} '
            '--cuda-device 0 --silent')
    elif exists(f'{dygiepp_path}/models/{model}'):
        model_run = (
            f'allennlp predict {dygiepp_path}/models/{model} '
            f'{formatted_data_path} --predictor dygie --include-package '
            f'dygie --use-dataset-reader --output-file {out_path} '
            '--cuda-device 0 --silent')
    out = subprocess.run(model_run, capture_output=True, shell=True)

    # Convert bytes to string so they can be written to a file
    stdout_s = out.stdout.decode("utf-8")
    stderr_s = out.stderr.decode("utf-8")

    # Save stdout
    with open(allen_out_path, 'w') as myf:
        myf.write('====> STDOUT <====\n\n')
        myf.write(stdout_s)
        myf.write('\n\n====> STDERR <====\n\n')
        myf.write(stderr_s)


def format_new_data(data, top_dir, out_prefix, dygiepp_path):
    """
    Format data for input to dygiepp. Saves results to formatted_data. Dataset
    name doesn't matter because it wil be changed to match the models.

    parameters:
        data, str: path to directory with raw abstracts
        top_dir, str: path to top level output dir
        out_prefix, str: prefix for data file
        dygiepp_path, str: path to dygiepp repo

    returns: formatted_data_path, the path to saved formatted data
    """
    # Define path to save formatted data
    formatted_data_path = f'{top_dir}/formatted_data/{out_prefix}_formatted_data.jsonl'

    # Define script path
    script_path = f'{dygiepp_path}/scripts/new-dataset/format_new_dataset.py'

    # Format data
    subprocess.run([
        "python", script_path, data, formatted_data_path, "scierc",
        "--use-scispacy"
    ])

    return formatted_data_path


def check_models(models_to_run, dygiepp_path):
    """
    Checks that all required models are downloaded in the dygiepp/pretrained
    directory. Raises an exception if one or more models are not found.

    parameters:
        models_to_run, list of str: list of mdoels to run
        dygiepp_path, str: path to dygiepp repo

    returns: None
    """
    for model in models_to_run:
        if f'{model}.tar.gz' not in listdir(f'{dygiepp_path}/pretrained'):
            if model not in listdir(f'{dygiepp_path}/models'):
                raise ModelNotFoundError(
                    'One or mode requested models has not '
                    'been downloaded to the dygiepp/pretrained directory. Please download '
                    'models and try again.')


def check_prefix(top_dir, out_prefix):
    """
    Checks if any files in the tree exist with the same file prefix, in order
    to prevent files from being overwritten. Raises an exception if any files
    are found with that prefix.

    parameters:
        top_dir, str: path to top directory for output file structure
        out_prefix, str: string to be prepended to all output files

    returns: None
    """
    for path, currentdir, files in walk(top_dir):
        for f in files:
            if f.startswith(out_prefix):
                raise PrefixError(
                    f'Files with prefix {out_prefix} already '
                    'exist in this file tree, please try again with a new prefix.'
                )


def check_make_filetree(top_dir):
    """
    Checks if the top_dir exists already, as well as the correct
    subdirectories. Creates any missing directories.

    parameters:
        top_dir, str: path to top directory for output file structure

    returns: True if top_dir exists, False otherwise
    """
    # Check if top_dir exists
    if exists(top_dir):

        # If it does, check for correct subdirectories
        formatted_data_path = f'{top_dir}/formatted_data'
        if not exists(formatted_data_path):
            makedirs(formatted_data_path)

        model_predictions_path = f'{top_dir}/model_predictions'
        if not exists(model_predictions_path):
            makedirs(model_predictions_path)

        allennlp_output_path = f'{top_dir}/allennlp_output'
        if not exists(allennlp_output_path):
            makedirs(allennlp_output_path)

        performance_path = f'{top_dir}/performance'
        if not exists(performance_path):
            makedirs(performance_path)

        return True

    else:

        makedirs(top_dir)
        makedirs(f'{top_dir}/formatted_data')
        makedirs(f'{top_dir}/model_predictions')
        makedirs(f'{top_dir}/allennlp_output')
        makedirs(f'{top_dir}/performance')

        return False


def main(top_dir, out_prefix, dygiepp_path, format_data, data,
         gold_standard, no_eval, models_to_run):

    # Check if the top_dir & other folders exist already
    verboseprint('\nChecking if file tree exists and creating it if not...')
    existed = check_make_filetree(top_dir)

    # Make sure no files with the same prefix exist
    verboseprint('\nMaking sure no files with the given prefix exist...')
    if existed:
        check_prefix(top_dir, out_prefix)

    # Check that requested models exist before starting
    verboseprint('\nMaking sure all requested models are downloaded...')
    check_models(models_to_run, dygiepp_path)

    # Format data
    if format_data:
        verboseprint('\nFormatting data...')
        formatted_data_path = format_new_data(data, top_dir, out_prefix,
                                              dygiepp_path)
    else:
        verboseprint('\nCopying formatted data into new file tree...')
        subprocess.run([
            "cp", data,
            f"{top_dir}/formatted_data/{out_prefix}_{basename(data)}"
        ])
        formatted_data_path = f'{top_dir}/formatted_data/{out_prefix}_{basename(data)}'

    # Run models
    verboseprint('\nRunning models...')
    for model in models_to_run:
        verboseprint(f'Running model {model}...')
        run_model(formatted_data_path, model, dygiepp_path, top_dir,
                  out_prefix)

    # Evaluate
    if not no_eval:
        verboseprint('\nEvaluating models...')
        evaluate_models(top_dir, gold_standard, out_prefix)

    verboseprint('\n\nDone!\n\n')


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run dygiepp models")

    parser.add_argument(
        'top_dir',
        type=str,
        help='Path to save the output of this script. A new filetree will '
        'be created here that includes sister dirs "formatted_data", '
        '"model_predictions", and "performance". The directory specified '
        'here can already exist, but will be created if it does not.')
    parser.add_argument(
        'out_prefix',
        type=str,
        help='Prefix to prepend to all output files from this script. '
        'This differentiates files that might be placed into the same '
        'filetree on different runs of this script on different data.')
    parser.add_argument('dygiepp_path',
                        type=str,
                        help='Path to dygiepp repository.')
    parser.add_argument(
        '--format_data',
        action='store_true',
        help='Whether or not to format data for prediction. If this flag '
        'is specified, a path to raw abstracts must be passed. Otherwise, '
        'a path to formatted data should be provided.')
    parser.add_argument(
        'data',
        type=str,
        help='Path to data. Processed if --format_data is not specified. '
        'If already formatted, file is copied to formatted_data to be '
        'manipulated (change dataset name) for model input.')
    parser.add_argument(
        '-gold_standard',
        type=str, default='',
        help='Path to gold standard for model evaulation. Models are '
        'evaluated using the script evaluate_model_output.py using simplest '
        'options if --no_eval is not passed.')
    parser.add_argument('--no_eval', action='store_true',
            help='Pass to skip evaluating the data.')
    parser.add_argument(
        '-models_to_run',
        nargs='+',
        help='List of models to run. Options are ace05-relation, scierc, '
        'scierc-lightweight, genia, genia-lightweight, chemprot, and pickle '
        'and seedev, if those models have been  trained. Default '
        'is all.',
        default=[
            'ace05-relation', 'scierc', 'scierc-lightweight', 'genia',
            'genia-lightweight', 'chemprot', 'pickle', 'seedev'
        ])
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Whether or not to print updates as the script runs.')

    args = parser.parse_args()

    args.top_dir = abspath(args.top_dir)
    args.data = abspath(args.data)
    args.dygiepp_path = abspath(args.dygiepp_path)
    args.gold_standard = abspath(args.gold_standard)

    verboseprint = print if args.verbose else lambda *a, **k: None

    main(args.top_dir, args.out_prefix, args.dygiepp_path, args.format_data,
         args.data,  args.gold_standard, args.no_eval, args.models_to_run)
