import pytest
import sbi.simulators as simulators
import sbi.utils as utils
import torch
from sbi import inference
from torch import distributions

# use cpu by default
torch.set_default_tensor_type("torch.FloatTensor")

# seed the simulations
torch.manual_seed(0)

# will be called by pytest. Then runs test_*(num_dim) for 1D and 3D


@pytest.mark.parametrize("num_dim", [1, 3])
def test_sre_on_linearGaussian_based_on_mmd(num_dim):

    dim, std = num_dim, 1.0
    simulator = simulators.LinearGaussianSimulator(dim=dim, std=std)
    prior = distributions.MultivariateNormal(
        loc=torch.zeros(dim), covariance_matrix=torch.eye(dim)
    )

    parameter_dim, observation_dim = dim, dim
    true_observation = torch.zeros(dim)

    # get classifier
    classifier = utils.get_classifier(
        "resnet",
        parameter_dim=simulator.parameter_dim,
        observation_dim=simulator.observation_dim,
    )

    # create inference method
    inference_method = inference.SRE(
        simulator=simulator,
        prior=prior,
        true_observation=true_observation,
        classifier=classifier,
        mcmc_method="slice-np",
    )

    # run inference
    inference_method.run_inference(num_rounds=1, num_simulations_per_round=1000)

    # draw samples from posterior
    samples = inference_method.sample_posterior(num_samples=1000)

    # define target distribution (analytically tractable) and sample from it
    target_samples = simulator.get_ground_truth_posterior_samples(1000)

    # compute the mmd
    mmd = utils.unbiased_mmd_squared(target_samples, samples)

    # check if mmd is larger than expected
    max_mmd = 0.02

    assert (
        mmd < max_mmd
    ), f"MMD={mmd} is more than 2 stds above the average performance."