import unittest

from app import scaleReplicas

class SimpleScaleTest(unittest.TestCase):
    
    def test_noScale(self):
        # this test checks for no scaling being done when within tolerance limit
        currentReplicas=10
        currentMetricValue= .85
        desiredMetricValue=.80
        tolerance=.1
        replicas = scaleReplicas(currentReplicas, currentMetricValue, desiredMetricValue, tolerance)

        self.assertEqual(currentReplicas, replicas)


    def test_upscale(self):
        # this test checks for up scaling
        currentReplicas=10
        currentMetricValue= .95
        desiredMetricValue=.80
        tolerance=.1
        replicas = scaleReplicas(currentReplicas, currentMetricValue, desiredMetricValue, tolerance)

        self.assertTrue(replicas>currentReplicas)

    def test_downScale(self):
        # this test checks for down scaling
        currentReplicas=10
        currentMetricValue= .55
        desiredMetricValue=.80
        tolerance=.1
        replicas = scaleReplicas(currentReplicas, currentMetricValue, desiredMetricValue, tolerance)

        self.assertTrue(replicas<currentReplicas)

if __name__ == "__main__":
    unittest.main()