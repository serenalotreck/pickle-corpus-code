"""
Script to run dygiepp models. Outputs into a directory structured as:

    chosen_dir_name
    |
    ├── formatted_data
    |
    ├── model_predictions
    |
    └── performance

Author: Serena G. Lotreck
"""
import argparse
from os.path import abspath, exists, basename
from os import makedirs, walki, listdir
import subprocess


class PrefixError(Exception):
    pass


class ModelNotFoundError(Exception):
    pass


def run_model(formatted_data_path, model, num_iter, dygiepp_path):
    """
    Run a dygiepp model with a given number of random seed iterations. Replaces
    the dataset name with the correct one for the model, and saves outputs to
    model_predictions directory.

    parameters:
        formatted_data_path, str: path to formatted data
        model, str: name of the model to run
        num_iter, int: number of times to run the model with a unique random
            seed
        dygiepp_path, str: path to dygiepp installation

    returns: None
    """
    # Use default random seed if only one iteration
    if num_iter == 1:
        pass
    ## PICK UP HERE


def format_data(data, top_dir, out_prefix, dygiepp_path):
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
    subprocess.run(["python", script_path, data, formatted_data_path, "scierc",
        "--use-scispacy"])

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
            raise ModelNotFoundError('One or mode requested models has not '
            'been downloaded to the dygiepp/pretrained directory. Please download '
            'models and try again.')


def check_prefix(top_dir, out_prefix):
    """
    Checks if any files in the tree exist with the same file prefix, in order
    to prevent files from being overwritte. Raises an exception if any files
    are found with that prefix.

    parameters:
        top_dir, str: path to top directory for output file structure
        out_prefix, str: string to be prepended to all output files

    returns: None
    """
    for path, currentdir, files in walk(top_dir):
        for f in files:
            if f.startswith(out_prefix):
                raise PrefixError(f'Files with prefix {out_prefix} already '
                'exist in this file tree, please try again with a new prefix.')


def check_make_filetree(top_dir, format_data):
    """
    Checks if the top_dir exists already, as well as the correct
    subdirectories. Creates any missing directories.

    parameters:
        top_dir, str: path to top directory for output file structure
        format_data, bool: whether or not to format raw data

    returns: True if top_dir exists, False otherwise
    """
    # Check if top_dir exists
    if exists(top_dir):

        # If it does, check for correct subdirectories
        formatted_data_path = f'{top_dir}/formatted_data'
        if not exists(formatted_data_path):

            # Make formatted_data directory if it doesn't exist and data
            # formatting has been requested
            makedirs(formatted_data_path)

        # Check for the other two:
        model_predictions_path = f'{top_dir}/model_predictions'
        if not exists(model_predictions_path):
            makedirs(model_predictions_path)

        performance_path = f'{top_dir}/performance'
        if not exists(performance_path):
            makedirs(performance_path)

        return True

    else:

        makedirs(top_dir)
        makedirs(f'{top_dir}/formatted_data')
        makedirs(f'{top_dir}/model_predictions')
        makedirs(f'{top_dir}/performance')

        return False


def main(top_dir, out_prefix, dygiepp_path, format_data, data, num_iter,
        gold_standard, models_to_run):

    # Check if the top_dir & other folders exist already
    existed = check_make_filetree(top_dir, format_data)

    # Make sure no files with the same prefix exist
    if existed:
        check_prefix(top_dir, out_prefix)

    # Check that requested models exist before starting
    check_models(models_to_run)

    # Format data
    if format_data:
        formatted_data_path = format_data(data, dygiepp_path)
    else:
        subprocess.run(["cp", data, f"{top_dir}/formatted_data/"])
        formatted_data_path = f'{top_dir}/formatted_data/{basename(data)}'

    # Run models
    for model in models_to_run:
        run_model(formatted_data_path, model, num_iter, dygiepp_path)

    # Evaluate


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run dygiepp models")

    parser.add_argument('top_dir', type=str,
            help='Path to save the output of this script. A new filetree will '
            'be created here that includes sister dirs "formatted_data", '
            '"model_predictions", and "performance". The directory specified '
            'here can already exist, but will be created if it does not.')
    parser.add_argument('out_prefix', type=str,
            help='Prefix to prepend to all output files from this script. '
            'This differentiates files that might be placed into the same '
            'filetree on different runs of this script on different data.')
    parser.add_argument('dygiepp_path', type=str,
            help='Path to dygiepp repository.')
    parser.add_argument('--format_data', action='store_true',
            help='Whether or not to format data for prediction. If this flag '
            'is specified, a path to raw abstracts must be passed. Otherwise, '
            'a path to formatted data should be provided.')
    parser.add_argument('data', type=str,
            help='Path to data. Processed if --format_data is not specified. '
            'If already formatted, file is copied to formatted_data to be '
            'manipulated (change dataset name) for model input.')
    parser.add_argument('-num_iter', type=int,
            help='Number of time to run models with different random seeds. '
            'Default is 1, in which case the default random seeds from '
            'DyGIE++ will be used.')
    parser.add_argument('gold_standard', type=str,
            help='Path to gold standard for model evaulation. Models are '
            'evaluated using the script evaluate_model_output.py.')
    parser.add_argument('models_to_run', nargs='+',
            help='List of models to run. Options are ace05, scierc, '
            'scierc-light, genia, and genia-light. Default is all.',
            default=['ace05', 'scierc', 'scierc-light', 'genia',
                'genia-light'])

    args = parser.parse_agrs()

    args.top_dir = abpath(args.top_dir)
    args.data = abspath(args.data)
    args.dygiepp_path = abspath(args.dygiepp_path)
    args.gold_standard = abspath(args.gold_standard)

    main(args.top_dir, args.out_prefix, args.dygiepp_path,
            args.format_data, args.data, args.num_iter, args.gold_standard,
            args.models_to_run)