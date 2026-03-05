package main

func quicksort(arr []int) []int {
    if len(arr) <= 1 {
        return arr
    }
    pivot := arr[len(arr)/2]
    var left, middle, right []int
    for _, v := range arr {
        if v < pivot {
            left = append(left, v)
        } else if v == pivot {
            middle = append(middle, v)
        } else {
            right = append(right, v)
        }
    }
    result := quicksort(left)
    result = append(result, middle...)
    result = append(result, quicksort(right)...)
    return result
}
