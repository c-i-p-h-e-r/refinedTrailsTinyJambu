#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

/*no-optimized date update function
Provided by TinyJAMBU Designers
*/
void state_update(unsigned int *state, const unsigned char *key, unsigned int number_of_steps)
{
	unsigned int i;
	unsigned int t1, t2, t3, t4, feedback;
	for (i = 0; i < (number_of_steps >> 5); i++)
	{
		t1 = (state[1] >> 15) | (state[2] << 17);  // 47 = 1*32+15
		t2 = (state[2] >> 6)  | (state[3] << 26);  // 47 + 23 = 70 = 2*32 + 6
		t3 = (state[2] >> 21) | (state[3] << 11);  // 47 + 23 + 15 = 85 = 2*32 + 21
		t4 = (state[2] >> 27) | (state[3] << 5);   // 47 + 23 + 15 + 6 = 91 = 2*32 + 27
		feedback = state[0] ^ t1 ^ (~(t2 & t3)) ^ t4 ^ ((unsigned int*)key)[i & 3];
 		// shift 32 bit positions
		state[0] = state[1]; state[1] = state[2]; state[2] = state[3];
		state[3] = feedback ;
	}
}

/*Helper Function: To print state*/
int printS(unsigned int* state)
{
	for (int i = 0; i < 4; i++)
		printf("%08x ", state[i]);
		printf("\n");
}

/*To switch parameters based on number of rounds*/
int get_params(int rounds, unsigned int *inDiff, unsigned int *outDiff, unsigned long int *limit)
{
	int power = 0;
	int index;

	unsigned int inputDiff[3][4] = {
		{0x00000000, 0x00000000, 0x00000000, 0x80000000}, //256
		{0x00000000, 0x00000000, 0x00000000, 0x04000000}, //320
		{0x00000000, 0x00000092, 0x20010000, 0x80000000}	//384
	};

	unsigned int outputDiff[3][4] = {
		{0x04080000, 0x01000002, 0x20000240, 0x80040010}, //256
		{0x81000012, 0x24000000, 0x90004000, 0x00010204}, //320
		{0x00000004, 0x00004080, 0x20001000, 0x81020000}  //384
	};

	switch(rounds)
	{
		case 256:
			power = 21;
			index = 0;
			break;
		case 320:
			power = 30;
			index = 1;
			break;
		case 384:
			power = 19;
			index = 2;
			break;
		default:
				return -1;
				break;
	}

	for (int i = 0; i < 4; i++)
	{
		inDiff[i] = inputDiff[index][i];
		outDiff[i] = outputDiff[index][i];
	}

	*limit = pow(2,power);
	return 0;
}

int main(int argc, char** argv)
{
	//Sanity check
	if(argc != 2)
	{
		printf("\nExcess or Insufficent Arguments. Exiting!\n");
		return 0;
	}
	unsigned long int j;
	unsigned int stateA[4];
	unsigned int stateB[4];
	unsigned int savedA[4];
	unsigned int savedB[4];

  unsigned int inputDiff[4];
  unsigned int outputDiff[4];

	unsigned int currentDiff[4];

	int Nr = atoi(argv[1]);
  unsigned long int limit;

	if(!get_params(Nr, inputDiff, outputDiff, &limit))
	{
		printf("\nConforming Pair Search:\n");
		printf("\nTarget Differential Trail\n");
		printS(inputDiff);
		printS(outputDiff);
	}
	else
	{
		printf("\nUnsupported Parameter.\n");
		return 0;
	}

	/*Considering a fixed key here.
	This can be randomized too*/
	const unsigned char *key = "000102030405060708090A0B0C0D0E0F";

	srand(time(NULL));   // Initialization for PRNG
	for (j=0; j<limit; j++){

		//initialize the stateA as random
		for (int i = 0; i < 4; i++) stateA[i] = rand(); // Returns a pseudo-random integer between 0 and RAND_MAX.

		//Generate second state with input difference
		for (int i = 0; i < 4; i++) stateB[i] =  stateA[i] ^ inputDiff[i];

		//Storing states for later use
		for (int i = 0; i < 4; i++) {
			savedA[i] = stateA[i];
			savedB[i] = stateB[i];
		}

		state_update(stateA, key, Nr);
		state_update(stateB, key, Nr);

		for (int i = 0; i < 4; i++) currentDiff[i] = stateA[i] ^ stateB[i];

		//Checking conformace to output difference
		if((currentDiff[0] == outputDiff[0]) &&
    (currentDiff[1] == outputDiff[1]) &&
    (currentDiff[2] == outputDiff[2]) &&
    (currentDiff[3] == outputDiff[3])){

			printf("\nInput States\n");
			printS(savedA);
			printS(savedB);

			printf("\nOutput States\n");
			printS(stateA);
			printS(stateB);
			}
		}

printf("\nDone\n");
}
