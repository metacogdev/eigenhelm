public class Fibonacci {
    public static long fibonacci(int n) {
        if (n <= 0) return 0;
        if (n == 1) return 1;
        long a = 0, b = 1;
        for (int i = 2; i <= n; i++) {
            long temp = b;
            b = a + b;
            a = temp;
        }
        return b;
    }

    public static long[] fibonacciSequence(int count) {
        long[] result = new long[count];
        for (int i = 0; i < count; i++) {
            result[i] = fibonacci(i);
        }
        return result;
    }
}
